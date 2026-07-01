"""Jobs API router — create, list, get, cancel."""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List
import uuid

from app.database import get_db
from app.models.job import SearchJob
from app.schemas.job import JobCreate, JobRead, JobUpdate
from app.services.queue_service import enqueue_job, get_job_status, queue_length
from app.config import settings

router = APIRouter()


@router.post("/", response_model=JobRead, status_code=201)
async def create_job(
    payload: JobCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Create and enqueue a scrape job."""
    job = SearchJob(
        location_id=payload.location_id,
        source_types=payload.source_types,
        keywords=payload.keywords,
        proxy_mode=payload.proxy_mode or "rotating_residential",
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    enqueue_job(settings.redis_queue_scrape, {"job_id": str(job.id)})
    return job


@router.get("/", response_model=List[JobRead])
async def list_jobs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SearchJob).order_by(desc(SearchJob.created_at)).limit(100))
    return result.scalars().all()


@router.get("/queue-stats", summary="Redis queue depths")
def queue_stats():
    return {
        "scrape_queue": queue_length(settings.redis_queue_scrape),
        "verify_queue": queue_length(settings.redis_queue_verify),
        "discovery_queue": queue_length(settings.redis_queue_discovery),
    }


@router.get("/{job_id}", response_model=JobRead)
async def get_job(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SearchJob).where(SearchJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(404, "Job not found")
    return job


@router.get("/{job_id}/status", summary="Live job status from Redis")
def job_live_status(job_id: uuid.UUID):
    status = get_job_status(str(job_id))
    if not status:
        raise HTTPException(404, "No live status found")
    return status


@router.patch("/{job_id}", response_model=JobRead)
async def update_job(job_id: uuid.UUID, payload: JobUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SearchJob).where(SearchJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(404, "Job not found")
    for k, v in payload.dict(exclude_none=True).items():
        setattr(job, k, v)
    await db.commit()
    await db.refresh(job)
    return job


@router.delete("/{job_id}", status_code=204)
async def cancel_job(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SearchJob).where(SearchJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(404, "Job not found")
    job.status = "cancelled"
    await db.commit()
