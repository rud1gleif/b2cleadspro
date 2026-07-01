"""System stats endpoint — queue depths, lead counts by country, job summaries."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.email_lead import EmailLead
from app.models.job import Job
from app.models.proxy import Proxy
from app.services.queue_service import queue_length
from app.config import settings

router = APIRouter()


@router.get("/overview", summary="High-level system stats")
def overview(db: Session = Depends(get_db)):
    total_leads = db.query(func.count(EmailLead.id)).scalar()
    verified_leads = db.query(func.count(EmailLead.id)).filter(EmailLead.is_verified == True).scalar()
    total_jobs = db.query(func.count(Job.id)).scalar()
    running_jobs = db.query(func.count(Job.id)).filter(Job.status == "running").scalar()
    active_proxies = db.query(func.count(Proxy.id)).filter(Proxy.is_active == True).scalar()

    return {
        "leads": {
            "total": total_leads,
            "verified": verified_leads,
            "unverified": total_leads - verified_leads,
        },
        "jobs": {
            "total": total_jobs,
            "running": running_jobs,
        },
        "proxies": {
            "active": active_proxies,
        },
        "queues": {
            "scrape": queue_length(settings.redis_queue_scrape),
            "verify": queue_length(settings.redis_queue_verify),
            "discovery": queue_length(settings.redis_queue_discovery),
        },
    }


@router.get("/leads-by-country", summary="Lead count grouped by country")
def leads_by_country(db: Session = Depends(get_db)):
    rows = (
        db.query(EmailLead.country_code, func.count(EmailLead.id).label("count"))
        .group_by(EmailLead.country_code)
        .order_by(func.count(EmailLead.id).desc())
        .limit(50)
        .all()
    )
    return [{"country_code": r.country_code, "count": r.count} for r in rows]


@router.get("/leads-by-niche", summary="Lead count grouped by niche")
def leads_by_niche(db: Session = Depends(get_db)):
    rows = (
        db.query(EmailLead.niche, func.count(EmailLead.id).label("count"))
        .filter(EmailLead.niche != None)
        .group_by(EmailLead.niche)
        .order_by(func.count(EmailLead.id).desc())
        .limit(30)
        .all()
    )
    return [{"niche": r.niche, "count": r.count} for r in rows]
