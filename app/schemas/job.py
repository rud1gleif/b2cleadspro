from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class JobCreate(BaseModel):
    locations: List[str] = Field(..., min_length=1)
    niches: Optional[List[str]] = None
    sources: List[str] = Field(default=["gmaps", "yelp", "yellowpages", "angi"])
    max_pages: int = Field(default=5, ge=1, le=50)
    concurrency: int = Field(default=3, ge=1, le=10)


class JobOut(BaseModel):
    id: int
    locations: str
    niches: Optional[str]
    sources: str
    max_pages: int
    concurrency: int
    status: str
    leads_found: int
    error: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
