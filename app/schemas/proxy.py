from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ProxyCreate(BaseModel):
    host: str
    port: int
    protocol: str = "http"
    username: Optional[str] = None
    password: Optional[str] = None
    country_code: Optional[str] = None


class ProxyRead(ProxyCreate):
    id: int
    is_active: bool
    latency_ms: Optional[int]
    fail_count: int
    success_count: int
    last_checked_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True
