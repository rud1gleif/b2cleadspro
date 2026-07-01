"""Bulk email re-verification worker.

Can be triggered:
  - Via the /api/verify/* endpoints
  - Via the Redis verify queue (queue_dispatcher.py)
  - Manually: python -m app.workers.verify_worker

Re-verification strategy:
  1. Query leads in batches (unverified first, then oldest-verified)
  2. For each lead, run the full verification pipeline
  3. Update lead fields: is_verified, mx_valid, is_disposable, score, is_reachable, verified_at
  4. Emit progress to Redis job_status cache
"""
import asyncio
from datetime import datetime, timezone
from typing import Optional
from loguru import logger
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.email_lead import EmailLead
from app.services.verification_service import verify_email
from app.services.queue_service import set_job_status
from app.config import settings

_BATCH_SIZE = 50  # leads per DB batch


def run_verify_batch(
    job_id: Optional[int] = None,
    limit: int = 1000,
    unverified_only: bool = False,
) -> dict:
    """
    Synchronous entry point for the queue dispatcher.
    Verifies up to `limit` leads (optionally filtered to unverified).
    Returns a summary dict.
    """
    return asyncio.run(_async_verify_batch(job_id, limit, unverified_only))


async def _async_verify_batch(
    job_id: Optional[int],
    limit: int,
    unverified_only: bool,
) -> dict:
    db: Session = SessionLocal()
    verified_count = 0
    failed_count = 0
    skipped_count = 0

    try:
        q = db.query(EmailLead)
        if job_id:
            q = q.filter(EmailLead.job_id == job_id)
        if unverified_only:
            q = q.filter(EmailLead.is_verified == False)
        q = q.order_by(EmailLead.id.asc()).limit(limit)
        leads = q.all()
        total = len(leads)
        logger.info(f"Verify batch: {total} leads (job_id={job_id}, limit={limit})")

        for i, lead in enumerate(leads):
            try:
                result = verify_email(
                    lead.email,
                    reacher_url=getattr(settings, "reacher_url", None),
                    reacher_api_key=getattr(settings, "reacher_api_key", None),
                )
                lead.syntax_ok      = result["syntax_ok"]
                lead.is_disposable  = result["is_disposable"]
                lead.mx_valid       = result["mx_ok"]
                lead.is_verified    = result["mx_ok"] and result["syntax_ok"] and not result["is_disposable"]
                lead.score          = result["score"]
                lead.is_reachable   = result["is_reachable"]
                lead.verified_at    = datetime.now(timezone.utc)
                verified_count += 1
            except Exception as e:
                logger.debug(f"Verify failed for {lead.email}: {e}")
                failed_count += 1

            # Commit in batches
            if (i + 1) % _BATCH_SIZE == 0:
                db.commit()
                progress = int(((i + 1) / total) * 100) if total else 100
                if job_id:
                    set_job_status(job_id, {
                        "status": "verifying",
                        "progress": progress,
                        "verified": verified_count,
                        "failed": failed_count,
                    })
                logger.debug(f"Verify progress: {i+1}/{total}")
                await asyncio.sleep(0)  # yield to event loop

        db.commit()

        summary = {
            "total": total,
            "verified": verified_count,
            "failed": failed_count,
            "skipped": skipped_count,
        }
        if job_id:
            set_job_status(job_id, {"status": "verify_done", "progress": 100, **summary})
        logger.info(f"Verify batch done: {summary}")
        return summary

    finally:
        db.close()
