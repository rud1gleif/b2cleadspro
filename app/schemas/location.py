from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid


class LocationCreate(BaseModel):
    raw_input: str
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class LocationRead(BaseModel):
    id: uuid.UUID
    raw_input: str
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    normalized: bool
    created_at: datetime

    class Config:
        from_attributes = True
