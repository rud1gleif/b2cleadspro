"""Visit a website URL and extract email addresses."""
import re
import httpx
from typing import Optional

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
BLOCKLIST = {"example.com", "sentry.io", "wix.com", "wordpress.com",
             "png", "jpg", "jpeg", "gif", "webp", "svg"}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


async def extract_email_from_site(url: str) -> Optional[str]:
    """Return the first clean email found on the given URL, or None."""
    if not url:
        return None
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True, headers=HEADERS) as client:
            r = await client.get(url)
            text = r.text
    except Exception:
        return None

    emails = EMAIL_RE.findall(text)
    for email in emails:
        domain = email.split("@")[-1].lower()
        ext = domain.split(".")[-1]
        if domain not in BLOCKLIST and ext not in BLOCKLIST:
            return email.lower()
    return None
