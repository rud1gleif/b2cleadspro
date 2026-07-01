from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid


class ProxyCreate(BaseModel):
    url: str
    provider: Optional[str] = None
    proxy_type: str = "datacenter"
    country: Optional[str] = None
    city: Optional[str] = None
    sticky_capable: bool = False


class ProxyRead(BaseModel):
    id: uuid.UUID
    url: str
    provider: Optional[str] = None
    proxy_type: str
    country: Optional[str] = None
    city: Optional[str] = None
    active: bool
    health_score: float
    avg_latency_ms: Optional[int] = None
    recent_failures: int
    created_at: datetime

    class Config:
        from_attributes = True
