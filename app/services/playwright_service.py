"""Playwright-based deep-crawler for JS-heavy pages."""
import asyncio
import re
from typing import Optional, List, Set
from loguru import logger

EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE,
)

BLOCKED_DOMAINS = {
    "example.com", "test.com", "sentry.io", "yourcompany.com",
    "domain.com", "email.com", "company.com", "wixpress.com",
    "squarespace.com", "shopify.com",
}

_browser = None
_playwright = None


async def get_browser():
    global _browser, _playwright
    if _browser is None or not _browser.is_connected():
        from playwright.async_api import async_playwright
        from app.config import settings
        _playwright = await async_playwright().start()
        _browser = await _playwright.chromium.launch(
            headless=settings.playwright_headless,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
            ],
        )
    return _browser


async def close_browser():
    global _browser, _playwright
    if _browser:
        await _browser.close()
        _browser = None
    if _playwright:
        await _playwright.stop()
        _playwright = None


async def fetch_with_playwright(
    url: str,
    proxy_url: Optional[str] = None,
    timeout_ms: int = 20000,
) -> Optional[str]:
    """Render a page fully (JS executed) and return the final HTML."""
    try:
        browser = await get_browser()
        context_opts = {"user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        if proxy_url:
            context_opts["proxy"] = {"server": proxy_url}
        context = await browser.new_context(**context_opts)
        page = await context.new_page()

        # Block images/fonts to speed up rendering
        await page.route("**/*.{png,jpg,jpeg,gif,svg,ico,woff,woff2,ttf}",
                         lambda r: r.abort())

        await page.goto(url, wait_until="networkidle", timeout=timeout_ms)
        content = await page.content()
        await context.close()
        return content
    except Exception as exc:
        logger.debug(f"Playwright fetch failed for {url}: {exc}")
        return None


def extract_emails_from_html(html: str) -> Set[str]:
    found = EMAIL_RE.findall(html)
    return {
        e.lower().strip()
        for e in found
        if e.split("@")[-1].lower() not in BLOCKED_DOMAINS and len(e) < 100
    }


async def deep_crawl(
    start_url: str,
    max_pages: int = 10,
    proxy_url: Optional[str] = None,
) -> dict:
    """
    Crawl start_url and up to max_pages same-domain sub-pages.
    Returns {"emails": set, "pages_crawled": int, "urls_visited": list}
    """
    from urllib.parse import urlparse, urljoin
    from html.parser import HTMLParser

    class LinkParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.links: List[str] = []
        def handle_starttag(self, tag, attrs):
            if tag == "a":
                for k, v in attrs:
                    if k == "href" and v:
                        self.links.append(v)

    base_netloc = urlparse(start_url).netloc
    visited: Set[str] = set()
    queue = [start_url]
    all_emails: Set[str] = set()
    pages_done = 0

    while queue and pages_done < max_pages:
        url = queue.pop(0)
        if url in visited:
            continue
        visited.add(url)
        html = await fetch_with_playwright(url, proxy_url)
        if not html:
            continue
        pages_done += 1
        all_emails.update(extract_emails_from_html(html))

        # Discover sub-links on same domain
        parser = LinkParser()
        parser.feed(html)
        for link in parser.links:
            full = urljoin(url, link)
            parsed = urlparse(full)
            if parsed.netloc == base_netloc and full not in visited and parsed.scheme in ("http", "https"):
                queue.append(full)

    return {
        "emails": all_emails,
        "pages_crawled": pages_done,
        "urls_visited": list(visited),
    }
