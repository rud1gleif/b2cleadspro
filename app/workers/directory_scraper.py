"""Directory scraper: Yelp, YellowPages, Angi.

Uses httpx + BeautifulSoup (no browser needed — these pages are server-rendered).
For each source it fetches paginated search results and extracts:
  name, phone, email, website, address.
"""
import asyncio
import re
from typing import List, Optional
import httpx
from bs4 import BeautifulSoup
from app.workers.email_extractor import extract_email_from_site

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def _text(tag) -> Optional[str]:
    """Safely get text from a BS4 tag, returns None if tag is None."""
    return tag.get_text(strip=True) if tag else None


# ---------------------------------------------------------------------------
# Yelp
# ---------------------------------------------------------------------------

async def _scrape_yelp_page(client: httpx.AsyncClient, query: str, location: str, offset: int) -> List[dict]:
    url = "https://www.yelp.com/search"
    params = {"find_desc": query, "find_loc": location, "start": offset}
    try:
        r = await client.get(url, params=params, timeout=15)
        soup = BeautifulSoup(r.text, "lxml")
    except Exception:
        return []

    leads = []
    for card in soup.select('li[class*="css-"] div[class*="businessName"]'):
        try:
            name_tag = card.find("a")
            name = _text(name_tag)
            parent = card.find_parent("li")
            phone_tag = parent.find("p", string=re.compile(r"\(?\d{3}\)?")) if parent else None
            phone = _text(phone_tag)
            addr_tag = parent.find("address") if parent else None
            address = addr_tag.get_text(" ", strip=True) if addr_tag else None
            leads.append({"name": name, "phone": phone, "address": address,
                          "email": None, "website": None, "rating": None, "category": None})
        except Exception:
            continue
    return leads


async def scrape_yelp(location: str, niche: str, max_pages: int = 3, **kwargs) -> List[dict]:
    results = []
    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
        for page in range(max_pages):
            batch = await _scrape_yelp_page(client, niche, location, offset=page * 10)
            if not batch:
                break
            results.extend(batch)
            await asyncio.sleep(1.5)
    for lead in results:
        lead["source"] = "yelp"
        lead["location"] = location
        lead["niche"] = niche
    return results


# ---------------------------------------------------------------------------
# YellowPages
# ---------------------------------------------------------------------------

async def _scrape_yp_page(client: httpx.AsyncClient, query: str, location: str, page: int) -> List[dict]:
    url = f"https://www.yellowpages.com/search?search_terms={query}&geo_location_terms={location}&page={page}"
    try:
        r = await client.get(url, timeout=15)
        soup = BeautifulSoup(r.text, "lxml")
    except Exception:
        return []

    leads = []
    for card in soup.select("div.result"):
        try:
            name = _text(card.select_one(".business-name span"))
            phone = _text(card.select_one(".phones"))
            address = _text(card.select_one(".street-address"))
            website_tag = card.select_one("a.track-visit-website")
            website = website_tag["href"] if website_tag else None
            leads.append({"name": name, "phone": phone, "address": address,
                          "website": website, "email": None, "rating": None, "category": None})
        except Exception:
            continue
    return leads


async def scrape_yellowpages(location: str, niche: str, max_pages: int = 3, **kwargs) -> List[dict]:
    results = []
    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
        for page in range(1, max_pages + 1):
            batch = await _scrape_yp_page(client, niche, location, page)
            if not batch:
                break
            tasks = [extract_email_from_site(lead["website"]) for lead in batch if lead.get("website")]
            emails = await asyncio.gather(*tasks, return_exceptions=True)
            ei = 0
            for lead in batch:
                if lead.get("website"):
                    lead["email"] = emails[ei] if not isinstance(emails[ei], Exception) else None
                    ei += 1
            results.extend(batch)
            await asyncio.sleep(1.5)
    for lead in results:
        lead["source"] = "yellowpages"
        lead["location"] = location
        lead["niche"] = niche
    return results


# ---------------------------------------------------------------------------
# Angi
# ---------------------------------------------------------------------------

async def _scrape_angi_page(client: httpx.AsyncClient, query: str, location: str, page: int) -> List[dict]:
    url = f"https://www.angi.com/companylist/{query.replace(' ', '-').lower()}/{location.replace(' ', '-').replace(',', '').lower()}-{page}.htm"
    try:
        r = await client.get(url, timeout=15)
        soup = BeautifulSoup(r.text, "lxml")
    except Exception:
        return []

    leads = []
    for card in soup.select("div.project-pro-info, div[class*='provider']"):
        try:
            name = _text(card.select_one("h2, h3, .company-name"))
            phone_tag = card.select_one("[class*='phone'], [href^='tel:']")
            phone = _text(phone_tag)
            addr_tag = card.select_one("[class*='address'], [class*='location']")
            address = addr_tag.get_text(" ", strip=True) if addr_tag else None
            rating_tag = card.select_one("[class*='rating'] [aria-label]")
            rating = None
            if rating_tag:
                m = re.search(r"([\d.]+)", rating_tag.get("aria-label", ""))
                rating = float(m.group(1)) if m else None
            leads.append({"name": name, "phone": phone, "address": address,
                          "rating": rating, "email": None, "website": None, "category": None})
        except Exception:
            continue
    return leads


async def scrape_angi(location: str, niche: str, max_pages: int = 3, **kwargs) -> List[dict]:
    results = []
    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
        for page in range(1, max_pages + 1):
            batch = await _scrape_angi_page(client, niche, location, page)
            if not batch:
                break
            results.extend(batch)
            await asyncio.sleep(1.5)
    for lead in results:
        lead["source"] = "angi"
        lead["location"] = location
        lead["niche"] = niche
    return results
