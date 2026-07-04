import csv
import io
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.lead import Lead
from app.schemas.lead import LeadOut

router = APIRouter(prefix="/api/leads", tags=["leads"])


@router.get("/", response_model=list[LeadOut])
async def list_leads(
    job_id: int = Query(...),
    source: str = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    q = select(Lead).where(Lead.job_id == job_id)
    if source:
        q = q.where(Lead.source == source)
    q = q.offset(skip).limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/export")
async def export_leads(
    job_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Lead).where(Lead.job_id == job_id))
    leads = result.scalars().all()
    if not leads:
        raise HTTPException(404, "No leads found for this job")

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
