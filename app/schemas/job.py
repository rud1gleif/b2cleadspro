from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum
import uuid


class JobStatus(str, Enum):
    pending = "pending"
    running = "running"
    done = "done"
    failed = "failed"
    cancelled = "cancelled"


class JobCreate(BaseModel):
    location_id: Optional[uuid.UUID] = None
    source_types: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    proxy_mode: Optional[str] = "rotating_residential"


class JobUpdate(BaseModel):
    status: Optional[JobStatus] = None
    error_message: Optional[str] = None


class JobRead(BaseModel):
    id: uuid.UUID
    location_id: Optional[uuid.UUID]
    status: str
    source_types: Optional[List[str]]
    keywords: Optional[List[str]]
    proxy_mode: str
    pages_discovered: int
    pages_scraped: int
    emails_found: int
    emails_verified: int
    error_message: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    finished_at: Optional[datetime]

    class Config:
        from_attributes = True
