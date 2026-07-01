"""Score Worker — reads queue:score, applies enrichment heuristics,
finalises lead score and writes it back to EmailLead.

Scoring factors:
  - MX valid          +40
  - SMTP confirmed    +15
  - Not disposable    +20
  - Not role account  +10
  - Has full name     +5
  - Known consumer domain (gmail/yahoo/hotmail/outlook) +5
  - Source is directory (yellowpages/yelp/clutch) +5
"""
import asyncio
from loguru import logger
from app.config import settings
from app.services.queue_service import pop
from app.database import SessionLocal
from app.models.email_lead import EmailLead

CONSUMER_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
    "icloud.com", "live.com", "msn.com", "me.com",
    "aol.com", "protonmail.com", "mail.com",
}

DIRECTORY_DOMAINS = {
    "yellowpages.com", "yelp.com", "clutch.co",
    "hotfrog.com", "cylex.us.com", "foursquare.com",
    "trustpilot.com", "bark.com", "thumbtack.com",
}


def compute_enriched_score(lead: EmailLead) -> int:
    score = 0

    if lead.mx_valid:
        score += 40

    # Verification record (latest)
    if lead.verifications:
        latest = sorted(lead.verifications, key=lambda v: v.checked_at, reverse=True)[0]
        if latest.smtp_ok is True:
            score += 15
        if not latest.is_disposable:
            score += 20
        if not latest.is_role_account:
            score += 10
    else:
        if not lead.is_disposable:
            score += 20

    if lead.full_name and len(lead.full_name.strip()) > 2:
        score += 5

    domain = lead.email.split("@")[-1].lower() if lead.email else ""
    if domain in CONSUMER_DOMAINS:
        score += 5

    if lead.source_domain and any(d in lead.source_domain for d in DIRECTORY_DOMAINS):
        score += 5

    return min(score, 100)


async def process_score_task(task: dict, db) -> None:
    lead_id = task["lead_id"]
    lead = (
        db.query(EmailLead)
        .filter(EmailLead.id == lead_id)
        .first()
    )
    if not lead:
        return
    lead.score = compute_enriched_score(lead)
    db.commit()


async def run():
    logger.info("[score] Worker started, waiting for tasks...")
    db = SessionLocal()
    try:
        while True:
            task = pop(settings.redis_queue_score, timeout=5)
            if task:
                try:
                    await process_score_task(task, db)
                except Exception as exc:
                    logger.exception(f"[score] task error: {exc}")
            else:
                await asyncio.sleep(0.1)
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(run())
