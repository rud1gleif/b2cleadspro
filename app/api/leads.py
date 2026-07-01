from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from app.database import get_db
from app.models.email_lead import EmailLead
from app.schemas.lead import LeadRead, LeadFilter
import csv
import io

router = APIRouter()


@router.get("/", response_model=dict)
def list_leads(
    country_code: Optional[str] = None,
    city: Optional[str] = None,
    niche: Optional[str] = None,
    is_verified: Optional[bool] = None,
    min_score: Optional[int] = None,
    job_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    q = db.query(EmailLead)
    if country_code:
        q = q.filter(EmailLead.country_code == country_code.upper())
    if city:
        q = q.filter(EmailLead.city.ilike(f"%{city}%"))
    if niche:
        q = q.filter(EmailLead.niche.ilike(f"%{niche}%"))
    if is_verified is not None:
        q = q.filter(EmailLead.is_verified == is_verified)
    if min_score is not None:
        q = q.filter(EmailLead.score >= min_score)
    if job_id:
        q = q.filter(EmailLead.job_id == job_id)

    total = q.count()
    rows = q.order_by(EmailLead.score.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "results": [LeadRead.from_orm(r) for r in rows],
    }


@router.get("/export", summary="Export leads as CSV")
def export_leads(
    country_code: Optional[str] = None,
    job_id: Optional[int] = None,
    is_verified: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    q = db.query(EmailLead)
    if country_code:
        q = q.filter(EmailLead.country_code == country_code.upper())
    if job_id:
        q = q.filter(EmailLead.job_id == job_id)
    if is_verified is not None:
        q = q.filter(EmailLead.is_verified == is_verified)

    rows = q.order_by(EmailLead.score.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "email", "full_name", "city", "region", "country", "country_code",
        "niche", "score", "is_verified", "mx_valid", "source_url", "job_id"
    ])
    for r in rows:
        writer.writerow([
            r.id, r.email, r.full_name, r.city, r.region, r.country, r.country_code,
            r.niche, r.score, r.is_verified, r.mx_valid, r.source_url, r.job_id
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads.csv"},
    )


@router.get("/{lead_id}", response_model=LeadRead)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    lead = db.query(EmailLead).filter(EmailLead.id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead not found")
    return lead
