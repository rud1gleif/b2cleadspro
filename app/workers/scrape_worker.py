"""Background scrape worker — orchestrates discovery + scrape + verify per SearchJob."""
import asyncio
import uuid
from datetime import datetime, timezone
from loguru import logger
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.job import SearchJob
from app.models.email_lead import EmailLead
from app.models.location import Location
from app.models.page import Page
from app.services.scraper_service import (
    fetch_page_async, extract_emails, build_search_urls
)
from app.services.playwright_service import render_page
from app.services.sitemap_service import discover_urls_for_domain
from app.services.verification_service import verify_email
from app.services.proxy_service import get_best_proxy, build_proxy_dict, rotate_on_failure
from app.services.queue_service import set_job_status
from app.config import settings

PLAYWRIGHT_DOMAINS = {
    "yelp.com", "yellowpages.com", "hotfrog.com", "foursquare.com",
    "thumbtack.com", "bark.com", "houzz.com", "angieslist.com",
}


def run_scrape_job(job_id: str) -> None:
    """Sync entry point called by FastAPI BackgroundTasks or queue dispatcher."""
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

    seed_entries = []
    for kw in (keywords if keywords else [None]):
        urls = build_search_urls(
            city=location.city or location.country,
            country=location.country,
            niche=kw,
        )
        seed_entries.extend([(u, location, kw) for u in urls])

    max_pages = 50
    semaphore = asyncio.Semaphore(5)
    pages_done = 0
    leads_found = 0

    async def process_url(url: str, loc: Location, niche):
        nonlocal pages_done, leads_found

        async with AsyncSessionLocal() as db:
            r = await db.execute(select(SearchJob).where(SearchJob.id == job_uuid))
            fresh_job = r.scalar_one_or_none()
            if fresh_job and fresh_job.status == "cancelled":
                return

        async with AsyncSessionLocal() as db:
            proxy = await get_best_proxy(db, loc.country_code)
        proxy_dict = build_proxy_dict(proxy)
        proxy_str = proxy_dict.get("http") if proxy_dict else None

        domain = url.split("/")[2] if "//" in url else ""
        needs_playwright = any(d in domain for d in PLAYWRIGHT_DOMAINS)

        async with semaphore:
            if needs_playwright:
                html = await render_page(url, proxy=proxy_str)
            else:
                html = await fetch_page_async(url, proxy_dict)

        if not html:
            if proxy:
                async with AsyncSessionLocal() as db:
                    await rotate_on_failure(proxy, db)
            return

        emails = extract_emails(html)
        pages_done += 1

        async with AsyncSessionLocal() as db:
            page_rec = Page(
                url=url,
                job_id=job_uuid,
                status_code=200,
                emails_found=len(emails),
            )
            db.add(page_rec)
            await db.flush()

            for email in emails:
                if email in seen_emails:
                    continue
                seen_emails.add(email)
                try:
                    vr = verify_email(email)
                except Exception:
                    vr = {"score": 0.0}
                lead = EmailLead(
                    email=email,
                    city=loc.city,
                    region=loc.region,
                    country=loc.country,
                    country_code=loc.country_code,
                    source_url=url,
                    source_page_id=page_rec.id,
                    lead_score=float(vr.get("score", 0.0)),
                    scraped_at=datetime.now(timezone.utc),
                )
                db.add(lead)
                leads_found += 1

            await db.commit()

        progress = min(int((pages_done / max(len(seed_entries), 1)) * 100), 99)
        set_job_status(str(job_id), {
            "status": "running",
            "progress": progress,
            "emails_found": leads_found,
            "pages_scraped": pages_done,
        })

    tasks = [process_url(u, loc, niche) for u, loc, niche in seed_entries[:max_pages]]
    await asyncio.gather(*tasks, return_exceptions=True)

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
