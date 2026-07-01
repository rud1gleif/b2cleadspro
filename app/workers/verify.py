"""Verify Worker — reads queue:verify, runs syntax+MX+disposable checks,
optionally calls Reacher for SMTP check, updates EmailLead + writes Verification record,
then pushes to queue:score.
"""
import asyncio
import httpx
from loguru import logger
from datetime import datetime, timezone
from app.config import settings
from app.services.queue_service import pop, push_score_task
from app.services.verification_service import verify_email
from app.database import SessionLocal
from app.models.email_lead import EmailLead
from app.models.verification import Verification


async def call_reacher(email: str) -> dict:
    """Call self-hosted Reacher for SMTP-level check. Returns {} on error/unavailable."""
    try:
        headers = {}
        if settings.reacher_api_key:
            headers["Authorization"] = settings.reacher_api_key
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(
                f"{settings.reacher_url}/v0/check_email",
                headers=headers,
                json={
                    "to_email": email,
                    "hello_name": "b2cleadspro.io",
                    "from_email": "verify@b2cleadspro.io",
                },
            )
            if r.status_code == 200:
                return r.json()
    except Exception as exc:
        logger.debug(f"[verify] Reacher unavailable: {exc}")
    return {}


def parse_reacher_result(data: dict) -> dict:
    """Normalise Reacher response into our fields."""
    if not data:
        return {"smtp_ok": None}
    is_reachable = data.get("is_reachable", "unknown")
    smtp = data.get("smtp", {})
    return {
        "smtp_ok": is_reachable == "safe",
        "mx_ok":   data.get("mx", {}).get("accepts_mail", None),
        "is_disposable": data.get("misc", {}).get("is_disposable", False),
    }


async def process_verify_task(task: dict, db) -> None:
    lead_id = task["lead_id"]
    email   = task["email"]

    lead = db.query(EmailLead).filter(EmailLead.id == lead_id).first()
    if not lead:
        return

    # Fast local checks
    vr = verify_email(email)

    # Optional Reacher SMTP check
    reacher_data = await call_reacher(email)
    reacher = parse_reacher_result(reacher_data)

    # Merge: Reacher overrides local where available
    mx_ok      = reacher.get("mx_ok")      if reacher.get("mx_ok") is not None else vr["mx_ok"]
    smtp_ok    = reacher.get("smtp_ok")
    disposable = reacher.get("is_disposable", False) or vr["is_disposable"]

    # Final score
    score = vr["score"]
    if smtp_ok is True:
        score = min(score + 15, 100)
    if smtp_ok is False:
        score = max(score - 20, 0)

    # Update lead
    lead.is_verified  = mx_ok
    lead.mx_valid     = mx_ok
    lead.is_disposable = disposable
    lead.score        = score

    # Write verification record
    rec = Verification(
        email_lead_id=lead_id,
        syntax_ok=vr["syntax_ok"],
        mx_ok=mx_ok,
        smtp_ok=smtp_ok,
        is_disposable=disposable,
        is_role_account=vr["is_role_account"],
        score=score,
        checked_at=datetime.now(timezone.utc),
    )
    db.add(rec)
    db.commit()

    # Forward to score queue for enrichment
    push_score_task(lead_id)


async def run():
    logger.info("[verify] Worker started, waiting for tasks...")
    db = SessionLocal()
    try:
        while True:
            task = pop(settings.redis_queue_verify, timeout=5)
            if task:
                try:
                    await process_verify_task(task, db)
                except Exception as exc:
                    logger.exception(f"[verify] task error: {exc}")
            else:
                await asyncio.sleep(0.1)
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(run())
