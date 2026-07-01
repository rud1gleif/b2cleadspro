from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class VerificationOut(BaseModel):
    verdict: Optional[str]
    syntax_valid: Optional[bool]
    dns_valid: Optional[bool]
    mx_valid: Optional[bool]
    smtp_valid: Optional[bool]
    is_disposable: Optional[bool]
    is_catch_all: Optional[bool]
    is_free_provider: Optional[bool]
    confidence: Optional[float]
    last_checked_at: datetime

    class Config:
        from_attributes = True


class LeadOut(BaseModel):
    id: UUID
    email: str
    name: Optional[str]
    phone: Optional[str]
    website: Optional[str]
    snippet: Optional[str]
    city: Optional[str]
    region: Optional[str]
    country: Optional[str]
    country_code: Optional[str]
    location_confidence: float
    lead_score: float
    is_suppressed: bool
    source_url: Optional[str]
    scraped_at: Optional[datetime]
    created_at: datetime
    verification: Optional[VerificationOut]

    class Config:
        from_attributes = True


class LeadFilter(BaseModel):
    country_code: Optional[str] = None
    city: Optional[str] = None
    verdict: Optional[str] = None  # safe | risky | invalid | unknown
    min_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    is_disposable: Optional[bool] = None
    include_suppressed: bool = False
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)
