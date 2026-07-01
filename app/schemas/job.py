from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class JobCreate(BaseModel):
    location: str = Field(..., description="City, region, or country to search")
    source_types: Optional[List[str]] = Field(
        default=["directories", "classifieds", "forums"],
        description="Source types to scrape",
    )
    keywords: Optional[List[str]] = Field(
        default=None, description="Optional keyword filters"
    )
    proxy_mode: Optional[str] = Field(
        default="rotating_residential",
        description="rotating_datacenter | rotating_residential | sticky_residential",
    )


class JobResponse(BaseModel):
    id: UUID
    status: str
    location_id: Optional[UUID]
    source_types: Optional[List[str]]
    keywords: Optional[List[str]]
    proxy_mode: str
    pages_discovered: int
    pages_scraped: int
    emails_found: int
    emails_verified: int
    error_message: Optional[str]
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True
