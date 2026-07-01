"""Core scraping helpers: URL discovery + email extraction."""
import re
import asyncio
from typing import List, Set, Optional
from urllib.parse import urlparse, urljoin
from loguru import logger

EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE,
)

BLOCKED_DOMAINS = {
    "example.com", "test.com", "sentry.io", "yourcompany.com",
    "domain.com", "email.com", "company.com",
}

SEED_TEMPLATES = [
    "site:{domain} email contact",
    '"{city}" "@gmail.com" OR "@yahoo.com" OR "@hotmail.com" contact',
    '"{city}" "{niche}" email contact',
]


def extract_emails(text: str) -> Set[str]:
    found = EMAIL_RE.findall(text)
    cleaned = set()
    for e in found:
        domain = e.split("@")[-1].lower()
        if domain not in BLOCKED_DOMAINS and len(e) < 100:
            cleaned.add(e.lower().strip())
    return cleaned


def build_search_urls(city: str, country: str, niche: Optional[str] = None) -> List[str]:
    """Return a list of Google search URLs for email discovery."""
    base = "https://www.google.com/search?q="
    queries = [
        f'site:yellowpages.com OR site:yelp.com "{city}" "{country}" email',
        f'"{city}" "{country}" "@gmail.com" OR "@yahoo.com" contact',
    ]
    if niche:
        queries.append(f'"{city}" "{niche}" email contact "{country}"')
    import urllib.parse
    return [base + urllib.parse.quote(q) for q in queries]


async def fetch_page_async(
    url: str,
    proxy_dict: Optional[dict] = None,
    timeout: int = 15,
) -> Optional[str]:
    """Async fetch using httpx; returns raw HTML text or None on error."""
    try:
        import httpx
        proxies = proxy_dict.get("http") if proxy_dict else None
        async with httpx.AsyncClient(proxies=proxies, timeout=timeout, follow_redirects=True) as client:
            r = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; B2CLeadsPro/1.0)",
                "Accept-Language": "en-US,en;q=0.9",
            })
            if r.status_code == 200:
                return r.text
    except Exception as exc:
        logger.debug(f"fetch_page_async failed for {url}: {exc}")
    return None


def extract_links(html: str, base_url: str, same_domain: bool = True) -> List[str]:
    """Extract all href links from raw HTML."""
    from html.parser import HTMLParser

    class LinkParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.links = []

        def handle_starttag(self, tag, attrs):
            if tag == "a":
                for attr, val in attrs:
                    if attr == "href" and val:
                        self.links.append(val)

    parser = LinkParser()
    parser.feed(html)
    base_parsed = urlparse(base_url)
    result = []
    for link in parser.links:
        full = urljoin(base_url, link)
        parsed = urlparse(full)
        if same_domain and parsed.netloc != base_parsed.netloc:
            continue
        if parsed.scheme in ("http", "https"):
            result.append(full)
    return list(set(result))
