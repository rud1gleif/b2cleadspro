"""Scrape Worker — reads queue:scrape, fetches pages, extracts emails,
persists EmailLead rows, pushes to queue:verify.

Uses httpx for most pages; falls back to Playwright for JS-heavy ones.
"""
import asyncio
import re
from loguru import logger
from datetime import datetime, timezone
from app.config import settings
from app.services.queue_service import pop, push_verify_task
from app.services.scraper_service import fetch_page_async, extract_emails
from app.services.playwright_service import fetch_with_playwright, extract_emails_from_html
from app.services.proxy_service import get_best_proxy, build_proxy_dict, rotate_on_failure
from app.database import SessionLocal
from app.models.email_lead import EmailLead
from app.models.job import Job
from app.models.page import Page

# Pages that typically require JS rendering
JS_HEAVY_PATTERNS = re.compile(
    r"(react|angular|vue|next|gatsby|svelte|nuxt)",
    re.IGNORECASE,
)


def _needs_playwright(html: str) -> bool:
    """Heuristic: if page has almost no content, retry with Playwright."""
    return len(html.strip()) < 2000 or JS_HEAVY_PATTERNS.search(html)


async def process_scrape_task(task: dict, db) -> int:
    """Returns count of new leads found."""
    job_id       = task["job_id"]
    url          = task["url"]
    country_code = task.get("country_code", "")
    city         = task.get("city", "")
    niche        = task.get("niche")

    # Check job not cancelled
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job or job.status == "cancelled":
        return 0

    proxy = get_best_proxy(db, country_code)
    proxy_dict = build_proxy_dict(proxy)
    proxy_url  = proxy_dict.get("http") if proxy_dict else None

    # Fetch with httpx first
    html = await fetch_page_async(url, proxy_dict)

    # If empty/JS-heavy, retry with Playwright
    if html and _needs_playwright(html):
        logger.debug(f"[scrape] Falling back to Playwright for {url}")
        html = await fetch_with_playwright(url, proxy_url) or html

    if not html:
        rotate_on_failure(proxy, db)
        page = Page(url=url, job_id=job_id, status_code=0, emails_found=0)
        db.add(page)
        db.commit()
        return 0

    emails = extract_emails(html)
    if not emails:
        emails = extract_emails_from_html(html)

    # Persist page record
    page = Page(url=url, job_id=job_id, status_code=200, emails_found=len(emails))
    db.add(page)

    new_leads = 0
    for email in emails:
        exists = db.query(EmailLead).filter(EmailLead.email == email).first()
        if exists:
            continue
        lead = EmailLead(
            email=email,
            city=city,
            country_code=country_code,
            niche=niche,
            source_url=url,
            source_domain=url.split("/")[2] if "//" in url else None,
            job_id=job_id,
            score=0,
            is_verified=False,
            is_disposable=False,
            mx_valid=False,
        )
        db.add(lead)
        db.flush()  # get lead.id before commit
        push_verify_task(lead.id, email)
        new_leads += 1

    # Update job counters
    if job:
        job.leads_found = (job.leads_found or 0) + new_leads
        job.pages_crawled = (job.pages_crawled or 0) + 1

    db.commit()
    return new_leads


async def run():
    logger.info("[scrape] Worker started, waiting for tasks...")
    db = SessionLocal()
    try:
        while True:
            task = pop(settings.redis_queue_scrape, timeout=5)
            if task:
                try:
                    found = await process_scrape_task(task, db)
                    if found:
                        logger.info(f"[scrape] {task['url'][:60]} → {found} new leads")
                except Exception as exc:
                    logger.exception(f"[scrape] task error: {exc}")
            else:
                await asyncio.sleep(0.1)
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(run())
