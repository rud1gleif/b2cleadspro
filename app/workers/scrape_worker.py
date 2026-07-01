"""FastAPI BackgroundTask entry point — now delegates to Redis queues.

When a job is created via the API, this function pushes discovery tasks
for each location+niche combo into queue:discovery, then the worker
pipeline handles the rest asynchronously.
"""
import json
from datetime import datetime, timezone
from loguru import logger
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.job import Job
from app.models.location import Location
from app.services.queue_service import push_discovery_job


def run_scrape_job(job_id: int) -> None:
    """Called by FastAPI BackgroundTasks. Enqueues discovery tasks into Redis."""
    db: Session = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job or job.status == "cancelled":
            return

        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        db.commit()

        location_ids = json.loads(job.location_ids) if isinstance(job.location_ids, str) else job.location_ids
        niches       = json.loads(job.niches)        if isinstance(job.niches, str)        else (job.niches or [])

        locations = db.query(Location).filter(Location.id.in_(location_ids)).all()
        if not locations:
            job.status = "failed"
            job.error_message = "No valid locations found for given IDs"
            db.commit()
            return

        tasks_pushed = 0
        for loc in locations:
            for niche in (niches if niches else [None]):
                push_discovery_job(
                    job_id=job.id,
                    location_id=loc.id,
                    city=loc.city or "",
                    country=loc.country,
                    country_code=loc.country_code,
                    niche=niche,
                )
                tasks_pushed += 1

        logger.info(f"Job {job_id}: pushed {tasks_pushed} discovery tasks into Redis queue.")
    except Exception as exc:
        logger.exception(f"run_scrape_job {job_id} failed: {exc}")
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
