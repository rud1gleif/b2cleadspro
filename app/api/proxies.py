from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.proxy import Proxy
from app.schemas.proxy import ProxyCreate, ProxyRead
from app.services.proxy_service import check_proxy_health

router = APIRouter()


@router.get("/", response_model=List[ProxyRead])
def list_proxies(db: Session = Depends(get_db)):
    return db.query(Proxy).order_by(Proxy.latency_ms.asc().nullslast()).all()


@router.post("/", response_model=ProxyRead, status_code=201)
def add_proxy(payload: ProxyCreate, db: Session = Depends(get_db)):
    existing = db.query(Proxy).filter(
        Proxy.host == payload.host, Proxy.port == payload.port
    ).first()
    if existing:
        return existing
    proxy = Proxy(**payload.dict())
    db.add(proxy)
    db.commit()
    db.refresh(proxy)
    return proxy


@router.post("/bulk", response_model=List[ProxyRead], status_code=201)
def add_proxies_bulk(payloads: List[ProxyCreate], db: Session = Depends(get_db)):
    created = []
    for p in payloads:
        existing = db.query(Proxy).filter(
            Proxy.host == p.host, Proxy.port == p.port
        ).first()
        if not existing:
            proxy = Proxy(**p.dict())
            db.add(proxy)
            created.append(proxy)
    db.commit()
    for c in created:
        db.refresh(c)
    return created


@router.delete("/{proxy_id}", status_code=204)
def delete_proxy(proxy_id: int, db: Session = Depends(get_db)):
    proxy = db.query(Proxy).filter(Proxy.id == proxy_id).first()
    if not proxy:
        raise HTTPException(404, "Proxy not found")
    db.delete(proxy)
    db.commit()


@router.post("/{proxy_id}/check", response_model=ProxyRead)
def health_check_proxy(proxy_id: int, db: Session = Depends(get_db)):
    proxy = db.query(Proxy).filter(Proxy.id == proxy_id).first()
    if not proxy:
        raise HTTPException(404, "Proxy not found")
    check_proxy_health(proxy, db)
    db.refresh(proxy)
    return proxy
