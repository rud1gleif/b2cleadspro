"""Background scrape worker — runs per job_id."""
import asyncio
import json
from datetime import datetime, timezone
from loguru import logger
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.job import Job
from app.models.email_lead import EmailLead
from app.models.location import Location
from app.models.page import Page
from app.services.scraper_service import (
    fetch_page_async, extract_emails, extract_links, build_search_urls
)
from app.services.verification_service import verify_email
from app.services.proxy_service import get_best_proxy, build_proxy_dict, rotate_on_failure


def run_scrape_job(job_id: int) -> None:
    """Entry point called by FastAPI BackgroundTasks."""
    asyncio.run(_async_run(job_id))


async def _async_run(job_id: int) -> None:
    db: Session = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job or job.status == "cancelled":
            return

        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        db.commit()

        location_ids = json.loads(job.location_ids) if isinstance(job.location_ids, str) else job.location_ids
        niches = json.loads(job.niches) if isinstance(job.niches, str) else (job.niches or [])

        locations = db.query(Location).filter(Location.id.in_(location_ids)).all()
        if not locations:
            job.status = "failed"
            job.error_message = "No valid locations found"
            db.commit()
            return

        seen_emails: set = set(
            r[0] for r in db.query(EmailLead.email).filter(
                EmailLead.job_id == job_id
            ).all()
        )

        total_urls = []
        for loc in locations:
            for niche in (niches if niches else [None]):
                urls = build_search_urls(
                    city=loc.city or loc.country,
                    country=loc.country,
                    niche=niche,
                )
                total_urls.extend([(url, loc, niche) for url in urls])

        max_pages = job.max_pages or 50
        concurrency = min(job.concurrency or 5, 10)
        semaphore = asyncio.Semaphore(concurrency)
        pages_done = 0
        leads_found = 0

        async def process_url(url: str, loc: Location, niche):
            nonlocal pages_done, leads_found
            if job.status == "cancelled":
                return
            proxy = get_best_proxy(db, loc.country_code)
            proxy_dict = build_proxy_dict(proxy)
            async with semaphore:
                html = await fetch_page_async(url, proxy_dict)
            if not html:
                rotate_on_failure(proxy, db)
                return

            emails = extract_emails(html)
            pages_done += 1

            # Persist page record
            page = Page(
                url=url,
                job_id=job_id,
                status_code=200,
                emails_found=len(emails),
            )
            db.add(page)

            for email in emails:
                if email in seen_emails:
                    continue
                seen_emails.add(email)
                vr = verify_email(email)
                lead = EmailLead(
                    email=email,
                    city=loc.city,
                    region=loc.region,
                    country=loc.country,
                    country_code=loc.country_code,
                    niche=niche,
                    source_url=url,
                    source_domain=url.split("/")[2] if "//" in url else None,
                    is_verified=vr["mx_ok"],
                    is_disposable=vr["is_disposable"],
                    mx_valid=vr["mx_ok"],
                    score=vr["score"],
                    job_id=job_id,
                )
                db.add(lead)
                leads_found += 1

            db.commit()

            # Progress update (throttled)
            progress = min(int((pages_done / max(len(total_urls), 1)) * 100), 99)
            job.progress = progress
            job.leads_found = leads_found
            job.pages_crawled = pages_done
            db.commit()

        tasks = [process_url(u, loc, niche) for u, loc, niche in total_urls[:max_pages]]
        await asyncio.gather(*tasks, return_exceptions=True)

        job.status = "done"
        job.progress = 100
        job.leads_found = leads_found
        job.pages_crawled = pages_done
        job.finished_at = datetime.now(timezone.utc)
        db.commit()
        logger.info(f"Job {job_id} done: {leads_found} leads from {pages_done} pages.")

    except Exception as exc:
        logger.exception(f"Job {job_id} crashed: {exc}")
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                job.status = "failed"
                job.error_message = str(exc)
                db.commit()
        except Exception:
            pass
    finally:
        db.close()
