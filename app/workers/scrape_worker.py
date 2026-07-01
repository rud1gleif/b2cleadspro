"""Background scrape worker — orchestrates discovery + scrape + verify per job."""
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
from app.services.playwright_service import render_page
from app.services.sitemap_service import discover_urls_for_domain
from app.services.verification_service import verify_email
from app.services.proxy_service import get_best_proxy, build_proxy_dict, rotate_on_failure
from app.services.queue_service import enqueue_job, set_job_status
from app.config import settings

# JS-heavy domains that need Playwright rendering
PLAYWRIGHT_DOMAINS = {
    "yelp.com", "yellowpages.com", "hotfrog.com", "foursquare.com",
    "thumbtack.com", "bark.com", "houzz.com", "angieslist.com",
}


def run_scrape_job(job_id: int) -> None:
    """Entry point called by FastAPI BackgroundTasks or queue dispatcher."""
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
        set_job_status(job_id, {"status": "running", "progress": 0})

        location_ids = json.loads(job.location_ids) if isinstance(job.location_ids, str) else job.location_ids
        niches = json.loads(job.niches) if isinstance(job.niches, str) else (job.niches or [])
        locations = db.query(Location).filter(Location.id.in_(location_ids)).all()

        if not locations:
            _fail_job(job, db, "No valid locations found")
            return

        # Collect all already-seen emails to avoid duplicates
        seen_emails: set = set(
            r[0] for r in db.query(EmailLead.email).all()
        )

        # Phase A: build seed URLs per location + niche
        seed_entries = []  # list of (url, loc, niche)
        for loc in locations:
            for niche in (niches if niches else [None]):
                urls = build_search_urls(
                    city=loc.city or loc.country,
                    country=loc.country,
                    niche=niche,
                )
                seed_entries.extend([(u, loc, niche) for u in urls])

        max_pages = job.max_pages or 50
        concurrency = min(job.concurrency or 5, 10)
        semaphore = asyncio.Semaphore(concurrency)
        pages_done = 0
        leads_found = 0

        async def process_url(url: str, loc: Location, niche):
            nonlocal pages_done, leads_found

            # Re-check cancellation
            fresh_job = db.query(Job).filter(Job.id == job_id).first()
            if fresh_job and fresh_job.status == "cancelled":
                return

            proxy = get_best_proxy(db, loc.country_code)
            proxy_dict = build_proxy_dict(proxy)
            proxy_str = proxy_dict.get("http") if proxy_dict else None

            # Choose renderer based on domain
            domain = url.split("/")[2] if "//" in url else ""
            needs_playwright = any(d in domain for d in PLAYWRIGHT_DOMAINS)

            async with semaphore:
                if needs_playwright:
                    html = await render_page(url, proxy=proxy_str)
                else:
                    html = await fetch_page_async(url, proxy_dict)

            if not html:
                rotate_on_failure(proxy, db)
                return

            emails = extract_emails(html)
            pages_done += 1

            # Persist page record
            page_rec = Page(
                url=url,
                job_id=job_id,
                status_code=200,
                emails_found=len(emails),
            )
            db.add(page_rec)

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
                    source_domain=domain or None,
                    is_verified=vr["mx_ok"],
                    is_disposable=vr["is_disposable"],
                    mx_valid=vr["mx_ok"],
                    score=vr["score"],
                    job_id=job_id,
                )
                db.add(lead)
                leads_found += 1

            db.commit()

            # Update progress
            total_expected = max(len(seed_entries), 1)
            progress = min(int((pages_done / total_expected) * 100), 99)
            job.progress = progress
            job.leads_found = leads_found
            job.pages_crawled = pages_done
            db.commit()
            set_job_status(job_id, {
                "status": "running",
                "progress": progress,
                "leads_found": leads_found,
                "pages_crawled": pages_done,
            })

        # Phase B: run seed URLs
        tasks = [process_url(u, loc, niche) for u, loc, niche in seed_entries[:max_pages]]
        await asyncio.gather(*tasks, return_exceptions=True)

        # Phase C: deep-crawl discovered domains via sitemap if budget remains
        remaining = max_pages - pages_done
        if remaining > 5:
            discovered_domains = set()
            for u, loc, niche in seed_entries:
                domain = u.split("/")[2] if "//" in u else ""
                if domain:
                    discovered_domains.add((domain, loc, niche))

            for domain, loc, niche in list(discovered_domains)[:5]:
                proxy = get_best_proxy(db, loc.country_code)
                proxy_dict = build_proxy_dict(proxy)
                try:
                    deep_urls = await discover_urls_for_domain(
                        domain, proxy_dict, max_urls=min(remaining, 40)
                    )
                    deep_tasks = [
                        process_url(du, loc, niche)
                        for du in deep_urls[:remaining]
                    ]
                    await asyncio.gather(*deep_tasks, return_exceptions=True)
                except Exception as e:
                    logger.debug(f"Deep crawl error for {domain}: {e}")

        # Done
        job.status = "done"
        job.progress = 100
        job.leads_found = leads_found
        job.pages_crawled = pages_done
        job.finished_at = datetime.now(timezone.utc)
        db.commit()
        set_job_status(job_id, {
            "status": "done",
            "progress": 100,
            "leads_found": leads_found,
            "pages_crawled": pages_done,
        })
        logger.info(f"Job {job_id} complete: {leads_found} leads / {pages_done} pages.")

    except Exception as exc:
        logger.exception(f"Job {job_id} crashed: {exc}")
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                _fail_job(job, db, str(exc))
        except Exception:
            pass
    finally:
        db.close()


def _fail_job(job: Job, db: Session, msg: str) -> None:
    job.status = "failed"
    job.error_message = msg
    job.finished_at = datetime.now(timezone.utc)
    db.commit()
    set_job_status(job.id, {"status": "failed", "error": msg})
