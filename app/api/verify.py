"""Email verification API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
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
    job_id: Optional[int] = None
    limit: int = 1000
    unverified_only: bool = False


# ---------- Routes ----------

@router.post("/single", summary="Verify a single email address")
def verify_single(payload: SingleVerifyRequest):
    """Run the full verification pipeline on one email and return the result."""
    result = verify_email(
        payload.email,
        reacher_url=getattr(settings, "reacher_url", None),
        reacher_api_key=getattr(settings, "reacher_api_key", None),
        skip_smtp=payload.skip_smtp,
    )
    return {"email": payload.email, **result}


@router.post("/bulk", summary="Verify a list of email addresses (max 500)")
def verify_bulk(payload: BulkVerifyRequest):
    """Verify up to 500 emails in one request. Returns per-email results."""
    if len(payload.emails) > 500:
        raise HTTPException(400, "Maximum 500 emails per bulk request.")
    results = []
    for email in payload.emails:
        r = verify_email(
            email,
            reacher_url=getattr(settings, "reacher_url", None),
            reacher_api_key=getattr(settings, "reacher_api_key", None),
            skip_smtp=payload.skip_smtp,
        )
        results.append({"email": email, **r})
    return {"count": len(results), "results": results}


@router.post("/re-verify", summary="Re-verify leads already in the database")
def re_verify_leads(
    payload: BulkReVerifyRequest,
    background_tasks: BackgroundTasks,
):
    """
    Queue or run a bulk re-verification pass over stored leads.
    Tries Redis queue first; falls back to BackgroundTask.
    """
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
    """Trigger an immediate refresh of the disposable-email domain blocklist."""
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
    return {
        "domain": domain,
        "is_disposable": is_disposable_domain(domain),
    }


@router.get("/lead/{lead_id}", summary="Get verification status of a stored lead")
def get_lead_verify_status(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(EmailLead).filter(EmailLead.id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead not found")
    return {
        "id": lead.id,
        "email": lead.email,
        "is_verified": lead.is_verified,
        "is_disposable": lead.is_disposable,
        "mx_valid": lead.mx_valid,
        "score": lead.score,
        "is_reachable": getattr(lead, "is_reachable", None),
        "verified_at": getattr(lead, "verified_at", None),
    }


@router.post("/lead/{lead_id}", summary="Re-verify a single stored lead")
def reverify_single_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(EmailLead).filter(EmailLead.id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead not found")
    from datetime import datetime, timezone
    result = verify_email(
        lead.email,
        reacher_url=getattr(settings, "reacher_url", None),
        reacher_api_key=getattr(settings, "reacher_api_key", None),
    )
    lead.syntax_ok     = result["syntax_ok"]
    lead.is_disposable = result["is_disposable"]
    lead.mx_valid      = result["mx_ok"]
    lead.is_verified   = result["mx_ok"] and result["syntax_ok"] and not result["is_disposable"]
    lead.score         = result["score"]
    lead.is_reachable  = result["is_reachable"]
    lead.verified_at   = datetime.now(timezone.utc)
    db.commit()
    return {"id": lead.id, "email": lead.email, **result}
