"""Jobs API router — create, list, get, cancel, and re-verify."""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.job import Job
from app.schemas.job import JobCreate, JobRead, JobUpdate
from app.workers.scrape_worker import run_scrape_job
from app.workers.verify_worker import run_verify_batch
from app.services.queue_service import enqueue_job, get_job_status, queue_length
from app.config import settings
import json

router = APIRouter()


@router.post("/", response_model=JobRead, status_code=201)
def create_job(
    payload: JobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Create and immediately enqueue a scrape job."""
    job = Job(
        status="pending",
        location_ids=json.dumps(payload.location_ids),
        niches=json.dumps(payload.niches or []),
        max_pages=payload.max_pages,
        concurrency=payload.concurrency,
        progress=0,
        leads_found=0,
        pages_crawled=0,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Try Redis queue first; fall back to BackgroundTask
    queued = enqueue_job(settings.redis_queue_scrape, {"job_id": job.id})
    if not queued:
        background_tasks.add_task(run_scrape_job, job.id)

    return _job_to_schema(job)


@router.get("/", response_model=List[JobRead])
def list_jobs(db: Session = Depends(get_db)):
    jobs = db.query(Job).order_by(Job.created_at.desc()).limit(100).all()
    return [_job_to_schema(j) for j in jobs]


@router.get("/queue-stats", summary="Redis queue depths")
def queue_stats():
    return {
        "scrape_queue": queue_length(settings.redis_queue_scrape),
        "verify_queue": queue_length(settings.redis_queue_verify),
        "discovery_queue": queue_length(settings.redis_queue_discovery),
    }


@router.get("/{job_id}", response_model=JobRead)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    return _job_to_schema(job)


@router.get("/{job_id}/status", summary="Live job status from Redis cache")
def job_live_status(job_id: int):
    status = get_job_status(job_id)
    if not status:
        raise HTTPException(404, "No live status found (Redis may be offline)")
    return status


@router.patch("/{job_id}", response_model=JobRead)
def update_job(job_id: int, payload: JobUpdate, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    for k, v in payload.dict(exclude_none=True).items():
        setattr(job, k, v)
    db.commit()
    db.refresh(job)
    return _job_to_schema(job)


@router.delete("/{job_id}", status_code=204)
def cancel_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    job.status = "cancelled"
    db.commit()


@router.post("/{job_id}/verify", summary="Re-verify all leads from this job")
def trigger_verify(
    job_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    queued = enqueue_job(settings.redis_queue_verify, {"job_id": job_id, "limit": 5000})
    if not queued:
        background_tasks.add_task(run_verify_batch, job_id=job_id, limit=5000)
    return {"message": f"Verification queued for job #{job_id}"}


def _job_to_schema(job: Job) -> JobRead:
    return JobRead(
        id=job.id,
        status=job.status,
        location_ids=json.loads(job.location_ids) if isinstance(job.location_ids, str) else job.location_ids,
        niches=json.loads(job.niches) if isinstance(job.niches, str) else job.niches,
        max_pages=job.max_pages,
        concurrency=job.concurrency,
        progress=job.progress,
        leads_found=job.leads_found,
        pages_crawled=job.pages_crawled,
        error_message=job.error_message,
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
    )
