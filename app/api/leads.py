import csv
import io
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.lead import Lead
from app.schemas.lead import LeadOut
from typing import Optional

router = APIRouter(prefix="/api/leads", tags=["leads"])

# Free consumer email providers — used for server-side filtering
FREE_EMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "outlook.com",
    "hotmail.com", "icloud.com", "live.com",
}

FREE_EMAIL_ALIASES = {
    "gmail": {"gmail.com"},
    "yahoo": {"yahoo.com", "ymail.com"},
    "outlook": {"outlook.com", "hotmail.com", "live.com"},
}


def _email_provider(email: str) -> Optional[str]:
    """Return the free-email bucket (gmail/yahoo/outlook) or None."""
    if not email:
        return None
    domain = email.strip().lower().split("@")[-1]
    for provider, domains in FREE_EMAIL_ALIASES.items():
        if domain in domains:
            return provider
    return None


@router.get("/", response_model=list[LeadOut])
async def list_leads(
    job_id: int = Query(...),
    source: str = Query(None, description="Filter by scrape source (gmaps, yelp, …)"),
    has_email: bool = Query(None, description="True → only leads WITH an email; False → only WITHOUT"),
    email_type: str = Query(
        None,
        description="Comma-separated free-email providers to match: gmail, yahoo, outlook. "
                    "Only considered when has_email=true.",
    ),
    skip: int = 0,
    limit: int = 5000,
    db: AsyncSession = Depends(get_db),
):
    q = select(Lead).where(Lead.job_id == job_id)

    if source:
        q = q.where(Lead.source == source)

    # has_email filter — done in DB so we don't pull 50k rows
    if has_email is True:
        q = q.where(Lead.email.isnot(None), Lead.email != "")
    elif has_email is False:
        q = q.where((Lead.email.is_(None)) | (Lead.email == ""))

    q = q.offset(skip).limit(limit)
    result = await db.execute(q)
    leads = result.scalars().all()

    # email_type post-filter (gmail / yahoo / outlook) — lightweight in Python
    if has_email is True and email_type:
        requested = {t.strip().lower() for t in email_type.split(",") if t.strip()}
        if requested:  # empty set means no filter
            leads = [
                lead for lead in leads
                if _email_provider(lead.email or "") in requested
            ]

    return leads


@router.get("/export")
async def export_leads(
    job_id: int = Query(...),
    has_email: bool = Query(None),
    email_type: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    q = select(Lead).where(Lead.job_id == job_id)
    if has_email is True:
        q = q.where(Lead.email.isnot(None), Lead.email != "")
    elif has_email is False:
        q = q.where((Lead.email.is_(None)) | (Lead.email == ""))

    result = await db.execute(q)
    leads = result.scalars().all()

    if has_email is True and email_type:
        requested = {t.strip().lower() for t in email_type.split(",") if t.strip()}
        if requested:
            leads = [
                lead for lead in leads
                if _email_provider(lead.email or "") in requested
            ]

    if not leads:
        raise HTTPException(404, "No leads found for this job with the given filters")

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        "id", "source", "name", "phone", "email",
        "website", "address", "rating", "category", "location", "niche"
    ])
    writer.writeheader()
    for lead in leads:
        writer.writerow({
            "id": lead.id, "source": lead.source, "name": lead.name,
            "phone": lead.phone, "email": lead.email, "website": lead.website,
            "address": lead.address, "rating": lead.rating,
            "category": lead.category, "location": lead.location, "niche": lead.niche,
        })
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=leads_job{job_id}.csv"},
    )
