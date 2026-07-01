from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
import uuid

from app.database import get_db
from app.models.proxy import Proxy
from app.schemas.proxy import ProxyCreate, ProxyRead

router = APIRouter()


@router.get("/count", summary="Count active proxies")
async def count_proxies(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(func.count(Proxy.id)).where(Proxy.active == True)
    )
    return {"active": result.scalar(), "total": (await db.execute(select(func.count(Proxy.id)))).scalar()}


@router.get("/", response_model=List[ProxyRead])
async def list_proxies(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Proxy).order_by(Proxy.health_score.desc())
    )
    return result.scalars().all()


@router.post("/", response_model=ProxyRead, status_code=201)
async def add_proxy(payload: ProxyCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Proxy).where(Proxy.url == payload.url))
    existing = result.scalar_one_or_none()
    if existing:
        return existing
    proxy = Proxy(**payload.dict())
    db.add(proxy)
    await db.commit()
    await db.refresh(proxy)
    return proxy


@router.post("/bulk", response_model=List[ProxyRead], status_code=201)
async def add_proxies_bulk(payloads: List[ProxyCreate], db: AsyncSession = Depends(get_db)):
    created = []
    for p in payloads:
        result = await db.execute(select(Proxy).where(Proxy.url == p.url))
        if not result.scalar_one_or_none():
            proxy = Proxy(**p.dict())
            db.add(proxy)
            created.append(proxy)
    await db.commit()
    for c in created:
        await db.refresh(c)
    return created


@router.delete("/{proxy_id}", status_code=204)
async def delete_proxy(proxy_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Proxy).where(Proxy.id == proxy_id))
    proxy = result.scalar_one_or_none()
    if not proxy:
        raise HTTPException(404, "Proxy not found")
    await db.delete(proxy)
    await db.commit()
