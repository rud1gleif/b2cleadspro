from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.location import Location
from app.schemas.location import LocationCreate, LocationRead
from app.services.location_service import resolve_location, list_countries

router = APIRouter()


@router.get("/countries", summary="List supported countries")
def get_countries():
    """Return the list of country names and codes from the bundled dataset."""
    return list_countries()


@router.get("/search", summary="Search locations (city, region, country)")
def search_locations(
    q: str = Query(..., min_length=2),
    db: Session = Depends(get_db),
):
    """Fuzzy-search the location table and return matches."""
    rows = (
        db.query(Location)
        .filter(
            Location.city.ilike(f"%{q}%")
            | Location.region.ilike(f"%{q}%")
            | Location.country.ilike(f"%{q}%")
        )
        .limit(20)
        .all()
    )
    return [LocationRead.from_orm(r) for r in rows]


@router.post("/", response_model=LocationRead, status_code=201)
def create_location(payload: LocationCreate, db: Session = Depends(get_db)):
    existing = (
        db.query(Location)
        .filter(
            Location.country_code == payload.country_code,
            Location.city == payload.city,
        )
        .first()
    )
    if existing:
        return existing
    loc = Location(**payload.dict())
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return loc


@router.get("/{location_id}", response_model=LocationRead)
def get_location(location_id: int, db: Session = Depends(get_db)):
    loc = db.query(Location).filter(Location.id == location_id).first()
    if not loc:
        raise HTTPException(404, "Location not found")
    return loc
