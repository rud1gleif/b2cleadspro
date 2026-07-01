from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    pending = "pending"
    running = "running"
    done = "done"
    failed = "failed"
    cancelled = "cancelled"


class JobCreate(BaseModel):
    location_ids: List[int]
    niches: Optional[List[str]] = None
    max_pages: Optional[int] = 50
    concurrency: Optional[int] = 5


class JobUpdate(BaseModel):
    status: Optional[JobStatus] = None
    progress: Optional[int] = None
    error_message: Optional[str] = None


class JobRead(BaseModel):
    id: int
    status: str
    location_ids: List[int]
    niches: Optional[List[str]]
    max_pages: int
    concurrency: int
    progress: int
    leads_found: int
    pages_crawled: int
    error_message: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    finished_at: Optional[datetime]

    class Config:
        from_attributes = True
