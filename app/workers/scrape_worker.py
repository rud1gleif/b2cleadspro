"""Background scrape worker — async, uses AsyncSessionLocal + SearchJob."""
import asyncio
import uuid
import urllib.parse
from datetime import datetime, timezone
from loguru import logger
from sqlalchemy import select
from app.database import AsyncSessionLocal, SessionLocal
from app.models.job import SearchJob
from app.models.email_lead import EmailLead
from app.models.location import Location
from app.models.page import Page
from app.services.scraper_service import fetch_page_async, extract_emails, extract_links
from app.services.playwright_service import render_page
from app.services.proxy_service import get_best_proxy, build_proxy_dict, rotate_on_failure
from app.services.queue_service import set_job_status
from app.config import settings

PLAYWRIGHT_DOMAINS = {
    "yelp.com", "yellowpages.com", "hotfrog.com", "foursquare.com",
    "thumbtack.com", "bark.com", "houzz.com", "angieslist.com",
}

# Direct directory seed templates — avoids Google blocking
DIRECTORY_SEEDS = [
    "https://www.yellowpages.com/search?term={niche_plus}&geo_location_terms={city_plus}+{country_plus}",
    "https://www.yelp.com/search?find_desc={niche_plus}&find_loc={city_plus}+{country_plus}",
    "https://www.cylex.us.com/search.html?q={niche_plus}&g={city_plus}",
    "https://www.hotfrog.com/search/{country_plus}/{city_plus}/{niche_plus}",
    "https://www.chamberofcommerce.com/search?q={niche_plus}&loc={city_plus}+{country_plus}",
    "https://www.manta.com/search?search_source=nav&search={niche_plus}+{city_plus}",
]


def _build_seed_urls(city: str, country: str, country_code: str, niche: str = None) -> list:
    """Build direct directory URLs — avoids Google blocking."""
    n = niche or "business"
    city_plus = urllib.parse.quote_plus(city)
    country_plus = urllib.parse.quote_plus(country)
    niche_plus = urllib.parse.quote_plus(n)

    seeds = []
    for tpl in DIRECTORY_SEEDS:
        try:
            seeds.append(tpl.format(
                niche_plus=niche_plus,
                city_plus=city_plus,
                country_plus=country_plus,
            ))
        except KeyError:
            pass

    # Google fallback — lower priority, may be blocked but worth trying
    base = "https://www.google.com/search?q="
    if niche:
        seeds.append(base + urllib.parse.quote(f'"{city}" "{niche}" email contact "{country}"'))
    seeds.append(base + urllib.parse.quote(f'"{city}" "{country}" "@gmail.com" OR "@yahoo.com" contact'))
    return seeds


def run_scrape_job(job_id: str) -> None:
    """Sync entry point called by BackgroundTasks or queue dispatcher."""
    asyncio.run(_async_run(job_id))


async def _async_run(job_id: str) -> None:
    job_uuid = uuid.UUID(str(job_id))

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(SearchJob).where(SearchJob.id == job_uuid))
        job = result.scalar_one_or_none()
        if not job or job.status == "cancelled":
            return
        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        await db.commit()
        location_id = job.location_id
        keywords = job.keywords or []
        max_pages = job.max_pages or 50

    set_job_status(str(job_id), {"status": "running", "progress": 0})

    async with AsyncSessionLocal() as db:
        loc_result = await db.execute(select(Location).where(Location.id == location_id))
        location = loc_result.scalar_one_or_none()

    if not location:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(SearchJob).where(SearchJob.id == job_uuid))
            job = result.scalar_one_or_none()
            if job:
                job.status = "failed"
                job.error_message = "No valid location found"
                job.finished_at = datetime.now(timezone.utc)
                await db.commit()
        set_job_status(str(job_id), {"status": "failed", "error": "No valid location found"})
        return

    async with AsyncSessionLocal() as db:
        seen_result = await db.execute(select(EmailLead.email))
        seen_emails: set = set(seen_result.scalars().all())

    # Build seed list using direct directory URLs
    seed_entries = []
    for kw in (keywords if keywords else [None]):
        urls = _build_seed_urls(
            city=location.city or location.country,
            country=location.country,
            country_code=location.country_code or "us",
            niche=kw,
        )
        seed_entries.extend([(u, location, kw) for u in urls])

    semaphore = asyncio.Semaphore(5)
    pages_done = 0
    leads_found = 0
    total_seeds = len(seed_entries[:max_pages])

    async def process_url(url: str, loc: Location, niche):
        nonlocal pages_done, leads_found

        # Check if job was cancelled
        async with AsyncSessionLocal() as db:
            r = await db.execute(select(SearchJob).where(SearchJob.id == job_uuid))
            fresh_job = r.scalar_one_or_none()
            if fresh_job and fresh_job.status == "cancelled":
                return

        # FIX: get_best_proxy is synchronous — use sync SessionLocal, NOT await
        proxy = None
        proxy_dict = None
        try:
            with SessionLocal() as sync_db:
                proxy = get_best_proxy(sync_db, loc.country_code)
                proxy_dict = build_proxy_dict(proxy)
        except Exception as e:
            logger.debug(f"Proxy lookup failed (no proxy): {e}")

        proxy_str = proxy_dict.get("http") if proxy_dict else None
        domain = url.split("/")[2] if "//" in url else ""
        needs_playwright = any(d in domain for d in PLAYWRIGHT_DOMAINS)

        async with semaphore:
            try:
                html = (
                    await render_page(url, proxy=proxy_str)
                    if needs_playwright
                    else await fetch_page_async(url, proxy_dict)
                )
            except Exception as e:
                logger.debug(f"Fetch error for {url}: {e}")
                html = None

        if not html:
            if proxy:
                try:
                    with SessionLocal() as sync_db:
                        rotate_on_failure(proxy, sync_db)
                except Exception:
                    pass
            logger.debug(f"[scrape] No HTML for {url} — skipping")
            return

        emails = extract_emails(html)
        pages_done += 1
        logger.info(f"[scrape] {url} → {len(emails)} emails")

        # Crawl same-domain links for additional email depth
        try:
            extra_links = extract_links(html, url, same_domain=True)[:5]
            for extra_url in extra_links:
                try:
                    extra_html = await fetch_page_async(extra_url, proxy_dict)
                    if extra_html:
                        emails.update(extract_emails(extra_html))
                except Exception:
                    pass
        except Exception:
            pass

        async with AsyncSessionLocal() as db:
            page_rec = Page(
                url=url,
                job_id=job_uuid,
                status_code=200,
                emails_found=len(emails),
            )
            db.add(page_rec)
            await db.flush()
            for email in list(emails):
                if email in seen_emails:
                    continue
                seen_emails.add(email)
                lead = EmailLead(
                    email=email,
                    city=loc.city,
                    region=loc.region,
                    country=loc.country,
                    country_code=loc.country_code,
                    source_url=url,
                    source_page_id=page_rec.id,
                    lead_score=0.5,
                    scraped_at=datetime.now(timezone.utc),
                )
                db.add(lead)
                leads_found += 1
            await db.commit()

        set_job_status(str(job_id), {
            "status": "running",
            "progress": min(int((pages_done / max(total_seeds, 1)) * 100), 99),
            "emails_found": leads_found,
            "pages_scraped": pages_done,
        })

    await asyncio.gather(
        *[process_url(u, loc, niche) for u, loc, niche in seed_entries[:max_pages]],
        return_exceptions=True,
    )

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(SearchJob).where(SearchJob.id == job_uuid))
        job = result.scalar_one_or_none()
        if job:
            job.status = "done"
            job.pages_scraped = pages_done
            job.emails_found = leads_found
            job.finished_at = datetime.now(timezone.utc)
            await db.commit()

    set_job_status(str(job_id), {
        "status": "done",
        "progress": 100,
        "emails_found": leads_found,
        "pages_scraped": pages_done,
    })
    logger.info(f"Job {job_id} complete: {leads_found} leads / {pages_done} pages.")
