"""Email verification API endpoints."""
import uuid
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional
from app.database import get_db
from app.models.email_lead import EmailLead
from app.services.verification_service import verify_email
from app.services.disposable_service import (
    refresh_disposable_list, disposable_domain_count, is_disposable_domain
)
from app.services.queue_service import enqueue_job
from app.workers.verify_worker import run_verify_batch
from app.config import settings

router = APIRouter()


# ---------- Schemas ----------

class SingleVerifyRequest(BaseModel):
    email: str
    skip_smtp: bool = False


class BulkVerifyRequest(BaseModel):
    emails: List[str]
    skip_smtp: bool = False


class BulkReVerifyRequest(BaseModel):
    job_id: Optional[str] = None
    limit: int = 1000
    unverified_only: bool = False


# ---------- Routes ----------

@router.post("/single", summary="Verify a single email address")
def verify_single(payload: SingleVerifyRequest):
    result = verify_email(
        payload.email,
        reacher_url=getattr(settings, "reacher_url", None),
        reacher_api_key=getattr(settings, "reacher_api_key", None),
    )
    return {"email": payload.email, **result}


@router.post("/bulk", summary="Verify a list of email addresses (max 500)")
def verify_bulk(payload: BulkVerifyRequest):
    if len(payload.emails) > 500:
        raise HTTPException(400, "Maximum 500 emails per bulk request.")
    results = [
        {"email": e, **verify_email(
            e,
            reacher_url=getattr(settings, "reacher_url", None),
            reacher_api_key=getattr(settings, "reacher_api_key", None),
        )}
        for e in payload.emails
    ]
    return {"count": len(results), "results": results}


@router.post("/re-verify", summary="Re-verify leads already in the database")
def re_verify_leads(payload: BulkReVerifyRequest, background_tasks: BackgroundTasks):
    queue_payload = {
        "job_id": payload.job_id,
        "limit": payload.limit,
        "unverified_only": payload.unverified_only,
    }
    queued = enqueue_job(settings.redis_queue_verify, queue_payload)
    if not queued:
        background_tasks.add_task(
            run_verify_batch,
            job_id=payload.job_id,
            limit=payload.limit,
            unverified_only=payload.unverified_only,
        )
    return {
        "message": "Re-verification queued.",
        "queued_via_redis": queued,
        "job_id": payload.job_id,
        "limit": payload.limit,
    }


@router.post("/refresh-blocklist", summary="Force-refresh the disposable-domain blocklist")
def refresh_blocklist(background_tasks: BackgroundTasks):
    background_tasks.add_task(refresh_disposable_list)
    return {
        "message": "Blocklist refresh triggered in background.",
        "current_count": disposable_domain_count(),
    }


@router.get("/blocklist/stats", summary="Disposable-domain blocklist statistics")
def blocklist_stats():
    return {
        "domain_count": disposable_domain_count(),
        "sources": [
            "disposable-email-domains/disposable-email-domains",
            "7c/fakefilter",
        ],
        "refresh_interval_hours": 24,
    }


@router.get("/blocklist/check", summary="Check if a domain is disposable")
def check_domain(domain: str = Query(..., description="Domain to check, e.g. mailinator.com")):
    return {"domain": domain, "is_disposable": is_disposable_domain(domain)}


@router.get("/lead/{lead_id}", summary="Get verification status of a stored lead")
async def get_lead_verify_status(lead_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(EmailLead).where(EmailLead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(404, "Lead not found")
    return {
        "id": lead.id,
        "email": lead.email,
        "lead_score": lead.lead_score,
        "is_suppressed": lead.is_suppressed,
        "location_confidence": lead.location_confidence,
    }


@router.post("/lead/{lead_id}", summary="Re-verify a single stored lead")
async def reverify_single_lead(lead_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(EmailLead).where(EmailLead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(404, "Lead not found")
    vr = verify_email(
        lead.email,
        reacher_url=getattr(settings, "reacher_url", None),
        reacher_api_key=getattr(settings, "reacher_api_key", None),
    )
    lead.lead_score = float(vr.get("score", lead.lead_score))
    await db.commit()
    return {"id": lead.id, "email": lead.email, **vr}
