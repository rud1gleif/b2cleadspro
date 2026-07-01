"""Disposable-domain detection with auto-updating blocklist.

Sources (all free, open-source):
  - https://raw.githubusercontent.com/disposable-email-domains/disposable-email-domains/master/disposable_email_blocklist.conf
  - https://raw.githubusercontent.com/7c/fakefilter/main/txt/data.txt

The list is cached in memory and refreshed on startup + every 24 hours.
Falls back to a small hardcoded seed list if the network is unavailable.
"""
import threading
import time
from typing import Set
from loguru import logger

_SOURCES = [
    "https://raw.githubusercontent.com/disposable-email-domains/disposable-email-domains/master/disposable_email_blocklist.conf",
    "https://raw.githubusercontent.com/7c/fakefilter/main/txt/data.txt",
]

_SEED_DOMAINS: Set[str] = {
    "mailinator.com", "guerrillamail.com", "10minutemail.com", "tempmail.com",
    "throwam.com", "yopmail.com", "trashmail.com", "fakeinbox.com",
    "sharklasers.com", "guerrillamailblock.com", "grr.la", "guerrillamail.info",
    "guerrillamail.biz", "guerrillamail.de", "guerrillamail.net", "guerrillamail.org",
    "spam4.me", "maildrop.cc", "dispostable.com", "discard.email",
    "spamgourmet.com", "spamgourmet.net", "spamgourmet.org",
    "mailnull.com", "spamspot.com", "spamthis.co.uk",
    "jetable.fr.nf", "jetable.net", "jetable.org", "jetable.pp.ua",
    "notsharingmy.info", "objectmail.com", "obobbo.com", "odaymail.com",
    "opentrash.com", "owlpic.com", "punkass.com", "qq.com",
    "r4nd0m.de", "rax.la", "razorwiresoftware.com",
    "rcpt.at", "recode.me", "recursor.net", "reddcoin.com",
}

_DISPOSABLE_DOMAINS: Set[str] = set(_SEED_DOMAINS)
_LOCK = threading.RLock()
_LAST_UPDATE: float = 0.0
_UPDATE_INTERVAL: float = 86400.0  # 24 hours


def _fetch_list(url: str) -> Set[str]:
    """Download a newline-separated domain list and return as a set."""
    import httpx
    try:
        resp = httpx.get(url, timeout=20, follow_redirects=True)
        if resp.status_code == 200:
            domains = set()
            for line in resp.text.splitlines():
                line = line.strip().lower()
                if line and not line.startswith("#") and "." in line:
                    domains.add(line)
            return domains
    except Exception as e:
        logger.warning(f"Failed to fetch disposable list from {url}: {e}")
    return set()


def refresh_disposable_list() -> int:
    """Download all sources and merge into the in-memory set. Returns count."""
    global _DISPOSABLE_DOMAINS, _LAST_UPDATE
    merged: Set[str] = set(_SEED_DOMAINS)
    for url in _SOURCES:
        fetched = _fetch_list(url)
        logger.info(f"Disposable list: {len(fetched)} domains from {url}")
        merged.update(fetched)
    with _LOCK:
        _DISPOSABLE_DOMAINS = merged
        _LAST_UPDATE = time.time()
    logger.info(f"Disposable blocklist refreshed: {len(merged)} total domains.")
    return len(merged)


def _auto_refresh_worker():
    """Background thread that refreshes the list every 24 hours."""
    while True:
        time.sleep(_UPDATE_INTERVAL)
        try:
            refresh_disposable_list()
        except Exception as e:
            logger.error(f"Auto-refresh disposable list failed: {e}")


def start_auto_refresh():
    """Start the background refresh thread (call once at startup)."""
    t = threading.Thread(target=_auto_refresh_worker, daemon=True, name="disposable-refresh")
    t.start()
    logger.info("Disposable-domain auto-refresh thread started (interval: 24h).")


def is_disposable_domain(domain: str) -> bool:
    """Return True if the domain is on the blocklist."""
    global _LAST_UPDATE
    # Lazy initial load
    if _LAST_UPDATE == 0.0:
        try:
            refresh_disposable_list()
        except Exception:
            pass  # use seed list
    with _LOCK:
        return domain.lower() in _DISPOSABLE_DOMAINS


def disposable_domain_count() -> int:
    """Return current size of the blocklist."""
    with _LOCK:
        return len(_DISPOSABLE_DOMAINS)
