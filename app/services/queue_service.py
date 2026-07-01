"""Redis queue helpers — thin wrapper around redis-py lists as FIFO queues."""
import json
import asyncio
from typing import Optional, Any
from loguru import logger

_redis_client = None


def get_redis():
    global _redis_client
    if _redis_client is None:
        import redis
        from app.config import settings
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


def push(queue_name: str, payload: Any) -> None:
    """Push a JSON-serialisable payload onto the right end of a list."""
    get_redis().rpush(queue_name, json.dumps(payload))


def pop(queue_name: str, timeout: int = 5) -> Optional[Any]:
    """Blocking pop from the left end; returns None on timeout."""
    result = get_redis().blpop(queue_name, timeout=timeout)
    if result:
        _, raw = result
        return json.loads(raw)
    return None


def qlen(queue_name: str) -> int:
    return get_redis().llen(queue_name)


def flush_queue(queue_name: str) -> None:
    get_redis().delete(queue_name)
    logger.info(f"Flushed queue: {queue_name}")


def push_discovery_job(job_id: int, location_id: int, city: str,
                       country: str, country_code: str,
                       niche: Optional[str] = None) -> None:
    from app.config import settings
    push(settings.redis_queue_discovery, {
        "job_id": job_id,
        "location_id": location_id,
        "city": city,
        "country": country,
        "country_code": country_code,
        "niche": niche,
    })


def push_scrape_task(job_id: int, url: str, location_id: int,
                     country_code: str, city: str,
                     niche: Optional[str] = None) -> None:
    from app.config import settings
    push(settings.redis_queue_scrape, {
        "job_id": job_id,
        "url": url,
        "location_id": location_id,
        "country_code": country_code,
        "city": city,
        "niche": niche,
    })


def push_verify_task(lead_id: int, email: str) -> None:
    from app.config import settings
    push(settings.redis_queue_verify, {"lead_id": lead_id, "email": email})


def push_score_task(lead_id: int) -> None:
    from app.config import settings
    push(settings.redis_queue_score, {"lead_id": lead_id})
