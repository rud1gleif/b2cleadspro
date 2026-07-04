"""Business data via OpenStreetMap Overpass API — routed through NordVPN.

Fully free, no API key, no blocks.
Uses Nominatim to geocode the location, then Overpass to fetch
businesses matching the niche within a radius.

Email enrichment: for every lead that has a website but no email in OSM tags,
we concurrently crawl the website via NordVPN to extract an email.
No cap — every lead with a website gets attempted.
"""
import asyncio
import re
import httpx
from typing import List, Optional
from app.workers.email_extractor import extract_email_from_site
from app.workers.proxy_config import PROXIES, BROWSER_HEADERS

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URL  = "https://overpass-api.de/api/interpreter"

NICHE_TAG_MAP = {
    "plumber":      'craft"="plumber',
    "electrician":  'craft"="electrician',
    "dentist":      'amenity"="dentist',
    "restaurant":   'amenity"="restaurant',
    "cafe":         'amenity"="cafe',
    "gym":          'leisure"="fitness_centre',
    "lawyer":       'amenity"="lawyers',
    "doctor":       'amenity"="doctors',
    "hair":         'shop"="hairdresser',
    "salon":        'shop"="beauty',
    "cleaner":      'shop"="dry_cleaning',
    "mechanic":     'shop"="car_repair',
    "real estate":  'office"="real_estate_agent',
    "insurance":    'office"="insurance',
    "accountant":   'office"="accountant',
    "veterinarian": 'amenity"="veterinary',
    "pharmacy":     'amenity"="pharmacy',
    "hotel":        'tourism"="hotel',
    "contractor":   'craft"="construction',
    "painter":      'craft"="painter',
}

HEADERS = {
    **BROWSER_HEADERS,
    "User-Agent": "B2CLeadsPro/1.0 (lead-generation-tool)",
}


def _niche_to_osm_filter(niche: str) -> str:
    if not niche:
        return 'amenity'
    niche_lower = niche.lower()
    for keyword, tag in NICHE_TAG_MAP.items():
        if keyword in niche_lower:
            return tag
    return f'name~"{re.escape(niche)}",i'


async def _geocode(location: str, client: httpx.AsyncClient) -> Optional[tuple]:
    try:
        r = await client.get(
            NOMINATIM_URL,
            params={"q": location, "format": "json", "limit": 1},
            timeout=15,
        )
        data = r.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        pass
    return None


async def _overpass_query(lat: float, lon: float, tag_filter: str, radius_m: int, client: httpx.AsyncClient) -> list:
    query = f"""
[out:json][timeout:30];
(
  node[{tag_filter}](around:{radius_m},{lat},{lon});
  way[{tag_filter}](around:{radius_m},{lat},{lon});
);
out center tags;
"""
    try:
        r = await client.post(OVERPASS_URL, data={"data": query}, timeout=45)
        return r.json().get("elements", [])
    except Exception:
        return []


def _extract_lead(el: dict, location: str, niche: str) -> Optional[dict]:
    tags = el.get("tags", {})
    name = tags.get("name")
    if not name:
        return None
    phone   = tags.get("phone") or tags.get("contact:phone")
    website = tags.get("website") or tags.get("contact:website")
    email   = tags.get("email") or tags.get("contact:email")
    street  = tags.get("addr:street", "")
    house   = tags.get("addr:housenumber", "")
    city    = tags.get("addr:city", location)
    address = " ".join(filter(None, [house, street, city])) or None
    category = (
        tags.get("amenity") or tags.get("shop") or
        tags.get("craft") or tags.get("office") or
        tags.get("tourism") or tags.get("leisure")
    )
    return {
        "source":   "gmaps",
        "name":     name,
        "phone":    phone,
        "email":    email,
        "website":  website,
        "address":  address,
        "rating":   None,
        "category": category,
        "location": location,
        "niche":    niche or None,
    }


async def scrape_gmaps(
    location: str,
    niche: str,
    max_results: int = 100,
    semaphore: Optional[asyncio.Semaphore] = None,
) -> List[dict]:
    results: List[dict] = []
    radius_m = min(500 + (max_results // 20) * 2000, 50000)

    async with httpx.AsyncClient(proxies=PROXIES, headers=HEADERS, follow_redirects=True) as client:
        coords = await _geocode(location, client)
        if not coords:
            return []
        lat, lon = coords

        tag_filter = _niche_to_osm_filter(niche)
        elements = await _overpass_query(lat, lon, tag_filter, radius_m, client)

        if not elements and niche:
            for tag_key in ["amenity", "shop", "craft", "office"]:
                elems = await _overpass_query(lat, lon, tag_key, radius_m, client)
                elements.extend(elems)
                if len(elements) >= max_results:
                    break

        # Build raw lead list first
        raw_leads: List[dict] = []
        for el in elements[:max_results]:
            lead = _extract_lead(el, location, niche)
            if lead:
                raw_leads.append(lead)

    # --- Concurrent email enrichment (no cap) ---
    # For every lead that has a website but no email in OSM tags,
    # fire off extract_email_from_site concurrently.
    enrich_sem = asyncio.Semaphore(8)  # max 8 concurrent site crawls

    async def _enrich(lead: dict) -> None:
        if lead.get("email") or not lead.get("website"):
            return
        async with enrich_sem:
            try:
                lead["email"] = await extract_email_from_site(lead["website"])
            except Exception:
                pass

    await asyncio.gather(*[_enrich(lead) for lead in raw_leads], return_exceptions=True)
    return raw_leads
