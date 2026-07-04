"""Job runner — dispatches scrape tasks and saves leads to the DB."""
import asyncio
import json
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.database import AsyncSessionLocal
from app.models.job import Job
from app.models.lead import Lead
from app.workers.gmaps_scraper import scrape_gmaps
from app.workers.directory_scraper import scrape_yelp, scrape_yellowpages, scrape_angi

SCRAPER_MAP = {
    "gmaps": scrape_gmaps,
    "yelp": scrape_yelp,
    "yellowpages": scrape_yellowpages,
    "angi": scrape_angi,
}


async def _save_leads(db: AsyncSession, job_id: int, leads: List[dict]) -> int:
    objs = [
        Lead(
            job_id=job_id,
            source=l.get("source", "unknown"),
            name=l.get("name"),
            phone=l.get("phone"),
            email=l.get("email"),
            website=l.get("website"),
            address=l.get("address"),
            rating=l.get("rating"),
            category=l.get("category"),
            location=l.get("location"),
            niche=l.get("niche"),
        )
        for l in leads
        if l.get("name")  # skip empty results
    ]
    db.add_all(objs)
    await db.commit()
    return len(objs)


async def run_job(job_id: int) -> None:
    async with AsyncSessionLocal() as db:
        job = await db.get(Job, job_id)
        if not job:
            return

        await db.execute(
            update(Job).where(Job.id == job_id).values(status="running")
        )
        await db.commit()

        try:
            locations: List[str] = json.loads(job.locations)
            niches: List[str] = [n.strip() for n in (job.niches or "").split(",") if n.strip()] or [""]
            sources: List[str] = [s.strip() for s in job.sources.split(",")]
            semaphore = asyncio.Semaphore(job.concurrency)
            total_leads = 0

            for location in locations:
                for niche in niches:
                    tasks = []
                    for source in sources:
                        fn = SCRAPER_MAP.get(source)
                        if not fn:
                            continue
                        if source == "gmaps":
                            # gmaps uses max_results (pages * 20 results per page)
                            tasks.append(fn(
                                location=location,
                                niche=niche,
                                max_results=job.max_pages * 20,
                                semaphore=semaphore,
                            ))
                        else:
                            # directory scrapers use max_pages
                            tasks.append(fn(
                                location=location,
                                niche=niche,
                                max_pages=job.max_pages,
                            ))

                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    all_leads = []
                    for r in results:
                        if isinstance(r, list):
                            all_leads.extend(r)
                    saved = await _save_leads(db, job_id, all_leads)
                    total_leads += saved
                    await db.execute(
                        update(Job).where(Job.id == job_id).values(leads_found=total_leads)
                    )
                    await db.commit()

            await db.execute(
                update(Job).where(Job.id == job_id).values(status="done", leads_found=total_leads)
            )
            await db.commit()

        except Exception as e:
            await db.execute(
                update(Job).where(Job.id == job_id).values(status="error", error=str(e))
            )
            await db.commit()
            raise
