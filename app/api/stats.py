"""System stats — queue depths, lead counts, job summaries."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.email_lead import EmailLead
from app.models.job import SearchJob
from app.models.proxy import Proxy
from app.services.queue_service import queue_length
from app.config import settings

router = APIRouter()


@router.get("/overview", summary="High-level system stats")
async def overview(db: AsyncSession = Depends(get_db)):
    total_leads = (await db.execute(select(func.count(EmailLead.id)))).scalar()
    suppressed = (await db.execute(
        select(func.count(EmailLead.id)).where(EmailLead.is_suppressed == True)
    )).scalar()
    total_jobs = (await db.execute(select(func.count(SearchJob.id)))).scalar()
    running_jobs = (await db.execute(
        select(func.count(SearchJob.id)).where(SearchJob.status == "running")
    )).scalar()
    active_proxies = (await db.execute(
        select(func.count(Proxy.id)).where(Proxy.active == True)
    )).scalar()

    return {
        "leads": {
            "total": total_leads,
            "active": total_leads - suppressed,
            "suppressed": suppressed,
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
async def leads_by_country(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(EmailLead.country_code, func.count(EmailLead.id).label("count"))
        .group_by(EmailLead.country_code)
        .order_by(func.count(EmailLead.id).desc())
        .limit(50)
    )
    return [{"country_code": r.country_code, "count": r.count} for r in result]
