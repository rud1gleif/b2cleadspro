"""Directory scraper: Yelp, YellowPages, Angi — routed through NordVPN SOCKS5.

Uses httpx + BeautifulSoup. All requests go through the Nord proxy.
Every lead with a website gets concurrent email extraction via extract_email_from_site.
"""
import asyncio
import re
from typing import List, Optional
import httpx
from bs4 import BeautifulSoup
from app.workers.email_extractor import extract_email_from_site
from app.workers.proxy_config import PROXIES, BROWSER_HEADERS


def _text(tag) -> Optional[str]:
    return tag.get_text(strip=True) if tag else None


def _client() -> httpx.AsyncClient:
    """Return an AsyncClient pre-configured with Nord proxy + browser headers."""
    return httpx.AsyncClient(
        proxies=PROXIES,
        headers=BROWSER_HEADERS,
        follow_redirects=True,
        timeout=20,
    )


async def _enrich_leads(leads: List[dict], max_concurrent: int = 8) -> None:
    """Concurrently crawl each lead's website and fill in missing emails."""
    sem = asyncio.Semaphore(max_concurrent)

    async def _fetch(lead: dict) -> None:
        if lead.get("email") or not lead.get("website"):
            return
        async with sem:
            try:
                lead["email"] = await extract_email_from_site(lead["website"])
            except Exception:
                pass

    await asyncio.gather(*[_fetch(lead) for lead in leads], return_exceptions=True)


# ---------------------------------------------------------------------------
# Yelp
# ---------------------------------------------------------------------------

async def _scrape_yelp_page(
    client: httpx.AsyncClient, query: str, location: str, offset: int
) -> List[dict]:
    url = "https://www.yelp.com/search"
    params = {"find_desc": query, "find_loc": location, "start": offset}
    try:
        r = await client.get(url, params=params)
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
            # Try to grab website link from the card
            website_tag = parent.find("a", href=re.compile(r"^https?://")) if parent else None
            website = website_tag["href"] if website_tag else None
            leads.append({
                "name": name, "phone": phone, "address": address,
                "email": None, "website": website, "rating": None, "category": None,
            })
        except Exception:
            continue
    return leads


async def scrape_yelp(location: str, niche: str, max_pages: int = 3, **kwargs) -> List[dict]:
    results = []
    async with _client() as client:
        for page in range(max_pages):
            batch = await _scrape_yelp_page(client, niche, location, offset=page * 10)
            if not batch:
                break
            results.extend(batch)
            await asyncio.sleep(1.5)

    # Tag metadata
    for lead in results:
        lead["source"] = "yelp"
        lead["location"] = location
        lead["niche"] = niche

    # Enrich ALL leads with websites (concurrent, NordVPN proxy)
    await _enrich_leads(results)
    return results


# ---------------------------------------------------------------------------
# YellowPages
# ---------------------------------------------------------------------------

async def _scrape_yp_page(
    client: httpx.AsyncClient, query: str, location: str, page: int
) -> List[dict]:
    url = f"https://www.yellowpages.com/search?search_terms={query}&geo_location_terms={location}&page={page}"
    try:
        r = await client.get(url)
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
            leads.append({
                "name": name, "phone": phone, "address": address,
                "website": website, "email": None, "rating": None, "category": None,
            })
        except Exception:
            continue
    return leads


async def scrape_yellowpages(location: str, niche: str, max_pages: int = 3, **kwargs) -> List[dict]:
    results = []
    async with _client() as client:
        for page in range(1, max_pages + 1):
            batch = await _scrape_yp_page(client, niche, location, page)
            if not batch:
                break
            results.extend(batch)
            await asyncio.sleep(1.5)

    for lead in results:
        lead["source"] = "yellowpages"
        lead["location"] = location
        lead["niche"] = niche

    # Enrich ALL leads with websites (concurrent, NordVPN proxy)
    await _enrich_leads(results)
    return results


# ---------------------------------------------------------------------------
# Angi
# ---------------------------------------------------------------------------

async def _scrape_angi_page(
    client: httpx.AsyncClient, query: str, location: str, page: int
) -> List[dict]:
    url = (
        f"https://www.angi.com/companylist/"
        f"{query.replace(' ', '-').lower()}/"
        f"{location.replace(' ', '-').replace(',', '').lower()}-{page}.htm"
    )
    try:
        r = await client.get(url)
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
            # Grab website link if present
            website_tag = card.select_one("a[href^='http']")
            website = website_tag["href"] if website_tag else None
            leads.append({
                "name": name, "phone": phone, "address": address,
                "rating": rating, "email": None, "website": website, "category": None,
            })
        except Exception:
            continue
    return leads


async def scrape_angi(location: str, niche: str, max_pages: int = 3, **kwargs) -> List[dict]:
    results = []
    async with _client() as client:
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

    # Enrich ALL leads with websites (concurrent, NordVPN proxy)
    await _enrich_leads(results)
    return results
