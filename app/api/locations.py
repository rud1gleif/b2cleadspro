from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import List
import uuid

from app.database import get_db
from app.models.location import Location
from app.schemas.location import LocationCreate, LocationRead

router = APIRouter()


@router.get("/search", response_model=List[LocationRead], summary="Search locations")
async def search_locations(
    q: str = Query(..., min_length=2),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Location).where(
            or_(
                Location.city.ilike(f"%{q}%"),
                Location.region.ilike(f"%{q}%"),
                Location.country.ilike(f"%{q}%"),
                Location.raw_input.ilike(f"%{q}%"),
            )
        ).limit(20)
    )
    return result.scalars().all()


@router.post("/", response_model=LocationRead, status_code=201)
async def create_location(payload: LocationCreate, db: AsyncSession = Depends(get_db)):
    loc = Location(**payload.dict())
    db.add(loc)
    await db.commit()
    await db.refresh(loc)
    return loc


@router.get("/{location_id}", response_model=LocationRead)
async def get_location(location_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Location).where(Location.id == location_id))
    loc = result.scalar_one_or_none()
    if not loc:
        raise HTTPException(404, "Location not found")
    return loc
