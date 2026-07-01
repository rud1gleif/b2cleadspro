from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
import csv
import io
import uuid

from app.database import get_db
from app.models.email_lead import EmailLead
from app.schemas.lead import LeadRead

router = APIRouter()


@router.get("/", response_model=dict)
async def list_leads(
    country_code: Optional[str] = None,
    city: Optional[str] = None,
    is_suppressed: Optional[bool] = False,
    min_score: Optional[float] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    q = select(EmailLead)
    if country_code:
        q = q.where(EmailLead.country_code == country_code.upper())
    if city:
        q = q.where(EmailLead.city.ilike(f"%{city}%"))
    if is_suppressed is not None:
        q = q.where(EmailLead.is_suppressed == is_suppressed)
    if min_score is not None:
        q = q.where(EmailLead.lead_score >= min_score)

    count_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = count_result.scalar()

    rows_result = await db.execute(
        q.order_by(EmailLead.lead_score.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = rows_result.scalars().all()
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "results": [LeadRead.model_validate(r) for r in rows],
    }


@router.get("/export", summary="Export leads as CSV")
async def export_leads(
    country_code: Optional[str] = None,
    is_suppressed: Optional[bool] = False,
    db: AsyncSession = Depends(get_db),
):
    q = select(EmailLead)
    if country_code:
        q = q.where(EmailLead.country_code == country_code.upper())
    if is_suppressed is not None:
        q = q.where(EmailLead.is_suppressed == is_suppressed)

    result = await db.execute(q.order_by(EmailLead.lead_score.desc()))
    rows = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "email", "name", "phone", "city", "region",
        "country", "country_code", "lead_score", "source_url", "scraped_at"
    ])
    for r in rows:
        writer.writerow([
            r.id, r.email, r.name, r.phone, r.city, r.region,
            r.country, r.country_code, r.lead_score, r.source_url, r.scraped_at
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads.csv"},
    )


@router.get("/{lead_id}", response_model=LeadRead)
async def get_lead(lead_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(EmailLead).where(EmailLead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(404, "Lead not found")
    return lead
