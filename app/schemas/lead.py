from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class LeadRead(BaseModel):
    id: int
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    full_name: Optional[str]
    city: Optional[str]
    region: Optional[str]
    country: Optional[str]
    country_code: Optional[str]
    source_url: Optional[str]
    source_domain: Optional[str]
    niche: Optional[str]
    score: int
    is_verified: bool
    is_disposable: bool
    mx_valid: bool
    created_at: datetime
    job_id: Optional[int]

    class Config:
        from_attributes = True


class LeadFilter(BaseModel):
    country_code: Optional[str] = None
    city: Optional[str] = None
    niche: Optional[str] = None
    is_verified: Optional[bool] = None
    min_score: Optional[int] = None
    job_id: Optional[int] = None
    page: int = 1
    page_size: int = 50
