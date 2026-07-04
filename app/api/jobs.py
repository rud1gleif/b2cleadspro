import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.database import get_db
from app.models.job import Job
from app.schemas.job import JobCreate, JobOut
from app.workers.job_runner import run_job

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("/", response_model=JobOut, status_code=201)
async def create_job(
    payload: JobCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    job = Job(
        locations=json.dumps(payload.locations),
        niches=",".join(payload.niches) if payload.niches else None,
        sources=",".join(payload.sources),
        max_pages=payload.max_pages,
        concurrency=payload.concurrency,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    background_tasks.add_task(run_job, job.id)
    return job


@router.get("/", response_model=list[JobOut])
async def list_jobs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job).order_by(desc(Job.created_at)).limit(50))
    return result.scalars().all()


@router.get("/{job_id}", response_model=JobOut)
async def get_job(job_id: int, db: AsyncSession = Depends(get_db)):
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job
