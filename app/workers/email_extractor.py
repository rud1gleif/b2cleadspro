"""Visit a website via NordVPN proxy and extract email addresses."""
import re
import httpx
from typing import Optional
from app.workers.proxy_config import PROXIES, BROWSER_HEADERS

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
BLOCKLIST = {
    "example.com", "sentry.io", "wix.com", "wordpress.com",
    "png", "jpg", "jpeg", "gif", "webp", "svg", "schema.org",
    "w3.org", "googleapis.com", "gstatic.com", "cloudflare.com",
    "amazon.com", "facebook.com", "twitter.com", "instagram.com",
    "tiktok.com", "youtube.com", "linkedin.com",
}

CONTACT_PATHS = ["/contact", "/contact-us", "/about", "/about-us", "/reach-us"]


def _pick_email(text: str) -> Optional[str]:
    emails = EMAIL_RE.findall(text)
    for email in emails:
        domain = email.split("@")[-1].lower()
        ext = domain.split(".")[-1]
        if domain not in BLOCKLIST and ext not in BLOCKLIST and len(ext) >= 2:
            return email.lower()
    return None


async def extract_email_from_site(url: str) -> Optional[str]:
    """Return the first clean email found on the site, routed through NordVPN."""
    if not url:
        return None
    base = url.rstrip("/")
    pages_to_try = [base] + [base + p for p in CONTACT_PATHS]

    try:
        async with httpx.AsyncClient(
            proxies=PROXIES,
            headers=BROWSER_HEADERS,
            timeout=12,
            follow_redirects=True,
        ) as client:
            for page_url in pages_to_try:
                try:
                    r = await client.get(page_url)
                    found = _pick_email(r.text)
                    if found:
                        return found
                except Exception:
                    continue
    except Exception:
        pass
    return None
