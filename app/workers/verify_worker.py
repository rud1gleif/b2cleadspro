"""Standalone batch verification worker for existing unverified leads."""
import asyncio
from loguru import logger
from app.database import SessionLocal
from app.models.email_lead import EmailLead
from app.models.verification import Verification
from app.services.verification_service import verify_email
from datetime import datetime, timezone


def run_verify_batch(job_id: int = None, limit: int = 1000) -> int:
    """Verify unverified leads for a job (or all) and persist Verification records."""
    db = SessionLocal()
    count = 0
    try:
        q = db.query(EmailLead).filter(EmailLead.is_verified == False)
        if job_id:
            q = q.filter(EmailLead.job_id == job_id)
        leads = q.limit(limit).all()

        for lead in leads:
            vr = verify_email(lead.email)
            lead.is_verified = vr["mx_ok"]
            lead.mx_valid = vr["mx_ok"]
            lead.is_disposable = vr["is_disposable"]
            lead.score = vr["score"]

            record = Verification(
                email_lead_id=lead.id,
                syntax_ok=vr["syntax_ok"],
                mx_ok=vr["mx_ok"],
                smtp_ok=vr["smtp_ok"],
                is_disposable=vr["is_disposable"],
                is_role_account=vr["is_role_account"],
                score=vr["score"],
                checked_at=datetime.now(timezone.utc),
            )
            db.add(record)
            count += 1

        db.commit()
        logger.info(f"Verified {count} leads.")
        return count
    finally:
        db.close()
