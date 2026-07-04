from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class LeadOut(BaseModel):
    id: int
    job_id: int
    source: str
    name: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    website: Optional[str]
    address: Optional[str]
    rating: Optional[float]
    category: Optional[str]
    location: Optional[str]
    niche: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
