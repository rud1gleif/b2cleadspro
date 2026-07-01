from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid


class LeadRead(BaseModel):
    id: uuid.UUID
    email: str
    name: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    snippet: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None
    location_confidence: float = 0.0
    lead_score: float = 0.0
    is_suppressed: bool = False
    source_url: Optional[str] = None
    scraped_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class LeadFilter(BaseModel):
    country_code: Optional[str] = None
    city: Optional[str] = None
    is_suppressed: Optional[bool] = None
    min_score: Optional[float] = None
    page: int = 1
    page_size: int = 50
