"""Async email harvester with recursive BFS crawl — routed through NordVPN.

Inspired by MailMiner's recursive approach but rebuilt with:
  - asyncio / httpx (concurrent, fast)
  - Domain-scoped crawling (never follows off-domain links)
  - NordVPN SOCKS5 proxy on every request
  - Deduplication of URLs and emails via sets
  - Configurable max-page cap (default 30 per site)
  - Returns ALL clean emails found, not just the first
"""
import asyncio
import re
from collections import deque
from typing import Optional, Set, List
from urllib.parse import urlparse, urljoin

import httpx
from bs4 import BeautifulSoup
from app.workers.proxy_config import PROXIES, BROWSER_HEADERS

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

EMAIL_BLOCKLIST: Set[str] = {
    # generic/system domains
    "example.com", "sentry.io", "wix.com", "wordpress.com",
    "schema.org", "w3.org", "googleapis.com", "gstatic.com",
    "cloudflare.com", "amazon.com",
    # social (never real business contacts)
    "facebook.com", "twitter.com", "instagram.com",
    "tiktok.com", "youtube.com", "linkedin.com",
    # image / asset extensions masquerading as emails
    "png", "jpg", "jpeg", "gif", "webp", "svg",
}

# Pages most likely to have contact emails — prioritised at the front of the queue
PRIORITY_PATHS = {"/contact", "/contact-us", "/about", "/about-us",
                  "/reach-us", "/get-in-touch", "/team", "/staff"}

# Extensions we skip entirely (binary / media assets)
SKIP_EXTENSIONS = {
    ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp",
    ".zip", ".mp4", ".mp3", ".css", ".js",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _domain(url: str) -> str:
    """Return the netloc (host) of a URL."""
    return urlparse(url).netloc.lower()


def _has_skip_ext(url: str) -> bool:
    path = urlparse(url).path.lower()
    return any(path.endswith(ext) for ext in SKIP_EXTENSIONS)


def _clean_emails(raw: List[str]) -> List[str]:
    """Filter out blocklisted / obviously fake emails."""
    out = []
    for email in raw:
        email = email.lower()
        domain = email.split("@")[-1]
        ext = domain.split(".")[-1]
        if domain not in EMAIL_BLOCKLIST and ext not in EMAIL_BLOCKLIST and len(ext) >= 2:
            out.append(email)
    return out


def _extract_links(html: str, base_url: str, target_domain: str) -> List[str]:
    """Parse all on-domain <a href> links from HTML."""
    soup = BeautifulSoup(html, "lxml")
    links = []
    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        absolute = urljoin(base_url, href).split("#")[0]  # strip fragments
        if _domain(absolute) == target_domain and not _has_skip_ext(absolute):
            links.append(absolute)
    return links


# ---------------------------------------------------------------------------
# Core crawler
# ---------------------------------------------------------------------------

async def _crawl(
    client: httpx.AsyncClient,
    start_url: str,
    max_pages: int,
) -> Set[str]:
    """BFS crawl of a single domain; return all email addresses found."""
    target_domain = _domain(start_url)
    visited: Set[str] = set()
    emails: Set[str] = set()

    # Seed: priority paths first, then root
    base = f"{urlparse(start_url).scheme}://{target_domain}"
    priority_urls = [base + p for p in PRIORITY_PATHS]
    queue: deque = deque([start_url] + priority_urls)

    while queue and len(visited) < max_pages:
        url = queue.popleft()
        if url in visited:
            continue
        visited.add(url)

        try:
            r = await client.get(url, timeout=12)
            if r.status_code not in (200, 201):
                continue
            html = r.text
        except Exception:
            continue

        # Extract emails from page
        raw = EMAIL_RE.findall(html)
        emails.update(_clean_emails(raw))

        # If we already have emails, we can be less aggressive about crawling
        if emails and len(visited) >= 5:
            # Still check remaining priority pages
            remaining_priority = [
                u for u in priority_urls if u not in visited
            ]
            if not remaining_priority:
                break
            queue.extendleft(reversed(remaining_priority))
            continue

        # Discover more on-domain links
        new_links = _extract_links(html, url, target_domain)
        for link in new_links:
            if link not in visited:
                queue.append(link)

        await asyncio.sleep(0.3)  # polite crawl delay

    return emails


# ---------------------------------------------------------------------------
# Public API (drop-in compatible with old extract_email_from_site)
# ---------------------------------------------------------------------------

async def extract_email_from_site(url: str, max_pages: int = 30) -> Optional[str]:
    """Return the best email found on the site via BFS crawl through NordVPN.

    Drop-in replacement for the old single-pass version.
    Returns the first clean business email found, or None.
    """
    all_emails = await extract_all_emails_from_site(url, max_pages=max_pages)
    return all_emails[0] if all_emails else None


async def extract_all_emails_from_site(
    url: str,
    max_pages: int = 30,
) -> List[str]:
    """Return ALL clean emails found on the site via BFS crawl through NordVPN."""
    if not url:
        return []
    # Normalise URL
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        async with httpx.AsyncClient(
            proxies=PROXIES,
            headers=BROWSER_HEADERS,
            follow_redirects=True,
            timeout=15,
        ) as client:
            found = await _crawl(client, url, max_pages=max_pages)
            # Sort: prefer shorter/simpler addresses (info@, hello@, contact@)
            return sorted(found, key=lambda e: (
                0 if e.split("@")[0] in {"info", "hello", "contact", "admin", "support", "office"}
                else 1,
                len(e),
            ))
    except Exception:
        return []
