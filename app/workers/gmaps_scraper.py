"""Business data via OpenStreetMap Overpass API.

Fully free, no API key, no scraping, no blocks.
Uses Nominatim to geocode the location, then Overpass to fetch
businesses matching the niche within a radius.
"""
import asyncio
import re
import httpx
from typing import List, Optional
from app.workers.email_extractor import extract_email_from_site

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URL  = "https://overpass-api.de/api/interpreter"

# Map common niche keywords → OSM amenity/shop/craft tags
NICHE_TAG_MAP = {
    "plumber":       'amenity"="plumber',
    "electrician":   'craft"="electrician',
    "dentist":       'amenity"="dentist',
    "restaurant":    'amenity"="restaurant',
    "cafe":          'amenity"="cafe',
    "gym":           'leisure"="fitness_centre',
    "lawyer":        'amenity"="lawyers',
    "doctor":        'amenity"="doctors',
    "hair":          'shop"="hairdresser',
    "salon":         'shop"="beauty',
    "cleaner":       'shop"="dry_cleaning',
    "mechanic":      'shop"="car_repair',
    "real estate":   'office"="real_estate_agent',
    "insurance":     'office"="insurance',
    "accountant":    'office"="accountant',
    "veterinarian":  'amenity"="veterinary',
    "pharmacy":      'amenity"="pharmacy',
    "hotel":         'tourism"="hotel',
    "contractor":    'craft"="construction',
    "painter":       'craft"="painter',
}

HEADERS = {
    "User-Agent": "B2CLeadsPro/1.0 (lead-generation-tool; contact: admin@example.com)",
    "Accept": "application/json",
}


def _niche_to_osm_filter(niche: str) -> str:
    """Convert a niche string to an OSM tag filter string."""
    if not niche:
        return 'amenity'
    niche_lower = niche.lower()
    for keyword, tag in NICHE_TAG_MAP.items():
        if keyword in niche_lower:
            return tag
    # Fallback: search by name keyword across all nodes/ways
    return f'name~"{re.escape(niche)}",i'


async def _geocode(location: str, client: httpx.AsyncClient) -> Optional[tuple]:
    """Return (lat, lon) for a location string using Nominatim."""
    try:
        r = await client.get(
            NOMINATIM_URL,
            params={"q": location, "format": "json", "limit": 1},
            headers=HEADERS,
            timeout=15,
        )
        data = r.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        pass
    return None


async def _overpass_query(lat: float, lon: float, tag_filter: str, radius_m: int, client: httpx.AsyncClient) -> list:
    """Run an Overpass QL query and return elements."""
    query = f"""
[out:json][timeout:30];
(
  node[{tag_filter}](around:{radius_m},{lat},{lon});
  way[{tag_filter}](around:{radius_m},{lat},{lon});
);
out center tags;
"""
    try:
        r = await client.post(OVERPASS_URL, data={"data": query}, headers=HEADERS, timeout=45)
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
    """Return business leads from OpenStreetMap for (location, niche)."""
    results: List[dict] = []
    # Radius scales with max_results (roughly 500m per 20 results, capped at 50km)
    radius_m = min(500 + (max_results // 20) * 2000, 50000)

    async with httpx.AsyncClient() as client:
        coords = await _geocode(location, client)
        if not coords:
            return []
        lat, lon = coords

        tag_filter = _niche_to_osm_filter(niche)
        elements   = await _overpass_query(lat, lon, tag_filter, radius_m, client)

        # If niche tag returned nothing, widen to a generic business search
        if not elements and niche:
            generic_filter = 'amenity,shop,craft,office,tourism,leisure'
            for tag_key in ["amenity", "shop", "craft", "office"]:
                elems = await _overpass_query(lat, lon, tag_key, radius_m, client)
                elements.extend(elems)
                if len(elements) >= max_results:
                    break

        # Enrich with emails from websites where missing
        enriched = 0
        for el in elements[:max_results]:
            lead = _extract_lead(el, location, niche)
            if not lead:
                continue
            if not lead["email"] and lead["website"] and enriched < 20:
                try:
                    lead["email"] = await extract_email_from_site(lead["website"])
                    enriched += 1
                except Exception:
                    pass
            results.append(lead)

    return results
