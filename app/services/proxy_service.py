"""Proxy rotation and health-check helpers."""
import time
import random
from typing import Optional
from sqlalchemy.orm import Session
from app.models.proxy import Proxy
from datetime import datetime, timezone

CHECK_URL = "http://httpbin.org/ip"


def get_best_proxy(db: Session, country_code: Optional[str] = None) -> Optional[Proxy]:
    """Return the fastest active proxy, optionally filtered by country."""
    q = db.query(Proxy).filter(Proxy.is_active == True)
    if country_code:
        q = q.filter(Proxy.country_code == country_code.upper())
    return q.order_by(Proxy.latency_ms.asc().nullslast(), Proxy.fail_count.asc()).first()


def build_proxy_dict(proxy: Optional[Proxy]) -> Optional[dict]:
    if not proxy:
        return None
    auth = ""
    if proxy.username and proxy.password:
        auth = f"{proxy.username}:{proxy.password}@"
    url = f"{proxy.protocol}://{auth}{proxy.host}:{proxy.port}"
    return {"http": url, "https": url}


def check_proxy_health(proxy: Proxy, db: Session) -> bool:
    import requests
    proxy_dict = build_proxy_dict(proxy)
    try:
        start = time.time()
        r = requests.get(CHECK_URL, proxies=proxy_dict, timeout=10)
        latency = int((time.time() - start) * 1000)
        if r.status_code == 200:
            proxy.is_active = True
            proxy.latency_ms = latency
            proxy.success_count = (proxy.success_count or 0) + 1
        else:
            proxy.fail_count = (proxy.fail_count or 0) + 1
            proxy.is_active = False
    except Exception:
        proxy.fail_count = (proxy.fail_count or 0) + 1
        proxy.is_active = proxy.fail_count < 5
    proxy.last_checked_at = datetime.now(timezone.utc)
    db.commit()
    return proxy.is_active


def rotate_on_failure(proxy: Optional[Proxy], db: Session) -> None:
    if proxy:
        proxy.fail_count = (proxy.fail_count or 0) + 1
        if proxy.fail_count >= 5:
            proxy.is_active = False
        db.commit()
