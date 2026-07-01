"""Discovery Worker — reads queue:discovery, finds target URLs, pushes to queue:scrape.

Strategy per task:
  1. Build seed search URLs for the location + niche.
  2. If Firecrawl is configured, use /map to expand each seed domain.
  3. Push all discovered page URLs into queue:scrape.
"""
import asyncio
import time
from loguru import logger
from app.config import settings
from app.services.queue_service import pop, push_scrape_task, qlen
from app.services.scraper_service import build_search_urls, fetch_page_async, extract_links
from app.services.firecrawl_service import firecrawl
from app.services.proxy_service import get_best_proxy, build_proxy_dict
from app.database import SessionLocal

# Known public directories worth seeding per location
SEED_DIRECTORIES = [
    "https://www.yellowpages.com/search?term={niche}&geo_location_terms={city}+{country}",
    "https://www.yelp.com/search?find_desc={niche}&find_loc={city}+{country}",
    "https://www.cylex.us.com/search.html?q={niche}&g={city}",
    "https://clutch.co/directory?q={niche}&location={city}",
    "https://www.hotfrog.com/search/{country}/{city}/{niche}",
]


def _build_seeds(city: str, country: str, country_code: str, niche: str = None) -> list:
    seeds = build_search_urls(city, country, niche)
    # Add directory seeds
    n = niche or "business"
    c_safe = city.replace(" ", "+")
    co_safe = country.replace(" ", "+")
    for tpl in SEED_DIRECTORIES:
        seeds.append(tpl.format(niche=n, city=c_safe, country=co_safe))
    return seeds


async def process_discovery_task(task: dict) -> int:
    """Returns number of scrape tasks enqueued."""
    job_id       = task["job_id"]
    location_id  = task["location_id"]
    city         = task.get("city") or task.get("country", "")
    country      = task.get("country", "")
    country_code = task.get("country_code", "")
    niche        = task.get("niche")

    db = SessionLocal()
    try:
        proxy = get_best_proxy(db, country_code)
        proxy_dict = build_proxy_dict(proxy)
    finally:
        db.close()

    seeds = _build_seeds(city, country, country_code, niche)
    enqueued = 0

    for seed_url in seeds:
        # Try Firecrawl /map first for domain expansion
        expanded_urls = []
        try:
            from urllib.parse import urlparse
            seed_domain = urlparse(seed_url).scheme + "://" + urlparse(seed_url).netloc
            if seed_domain not in ("https://www.google.com", "http://www.google.com"):
                expanded_urls = await firecrawl.map(seed_url, search=niche)
        except Exception:
            pass

        # Fallback: fetch seed page and extract links
        if not expanded_urls:
            html = await fetch_page_async(seed_url, proxy_dict)
            if html:
                expanded_urls = extract_links(html, seed_url, same_domain=False)
                expanded_urls = [seed_url] + expanded_urls[:15]
            else:
                expanded_urls = [seed_url]

        for url in expanded_urls[:20]:
            push_scrape_task(
                job_id=job_id,
                url=url,
                location_id=location_id,
                country_code=country_code,
                city=city,
                niche=niche,
            )
            enqueued += 1

    logger.info(f"[discovery] job={job_id} location={city} niche={niche} → {enqueued} URLs enqueued")
    return enqueued


async def run():
    logger.info("[discovery] Worker started, waiting for tasks...")
    while True:
        task = pop(settings.redis_queue_discovery, timeout=5)
        if task:
            try:
                await process_discovery_task(task)
            except Exception as exc:
                logger.exception(f"[discovery] task error: {exc}")
        else:
            await asyncio.sleep(0.1)


if __name__ == "__main__":
    asyncio.run(run())
