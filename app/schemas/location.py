from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class LocationCreate(BaseModel):
    city: Optional[str] = None
    region: Optional[str] = None
    country: str
    country_code: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class LocationRead(LocationCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
