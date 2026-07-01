"""Bulk email re-verification worker — async, uses AsyncSessionLocal."""
import asyncio
from typing import Optional
from loguru import logger
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.email_lead import EmailLead
from app.services.verification_service import verify_email
from app.services.queue_service import set_job_status
from app.config import settings

_BATCH_SIZE = 50


def run_verify_batch(
    job_id: Optional[str] = None,
    limit: int = 1000,
    unverified_only: bool = False,
) -> dict:
    """Sync entry point for queue dispatcher / BackgroundTasks."""
    return asyncio.run(_async_verify_batch(job_id, limit, unverified_only))


async def _async_verify_batch(
    job_id: Optional[str],
    limit: int,
    unverified_only: bool,
) -> dict:
    verified_count = 0
    failed_count = 0

    async with AsyncSessionLocal() as db:
        q = select(EmailLead)
        if unverified_only:
            q = q.where(EmailLead.is_suppressed == False)
        q = q.order_by(EmailLead.created_at.asc()).limit(limit)
        result = await db.execute(q)
        leads = result.scalars().all()

    total = len(leads)
    logger.info(f"Verify batch: {total} leads (limit={limit})")

    async with AsyncSessionLocal() as db:
        for i, lead in enumerate(leads):
            try:
                result = verify_email(
                    lead.email,
                    reacher_url=getattr(settings, "reacher_url", None),
                    reacher_api_key=getattr(settings, "reacher_api_key", None),
                )
                lead.lead_score = float(result.get("score", lead.lead_score))
                db.add(lead)
                verified_count += 1
            except Exception as e:
                logger.debug(f"Verify failed for {lead.email}: {e}")
                failed_count += 1

            if (i + 1) % _BATCH_SIZE == 0:
                await db.commit()
                progress = int(((i + 1) / total) * 100) if total else 100
                if job_id:
                    set_job_status(job_id, {
                        "status": "verifying",
                        "progress": progress,
                        "verified": verified_count,
                        "failed": failed_count,
                    })
                await asyncio.sleep(0)

        await db.commit()

    summary = {"total": total, "verified": verified_count, "failed": failed_count}
    if job_id:
        set_job_status(job_id, {"status": "verify_done", "progress": 100, **summary})
    logger.info(f"Verify batch done: {summary}")
    return summary
