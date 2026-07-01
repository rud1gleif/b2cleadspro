"""Redis queue helpers — enqueue / dequeue / status for scrape jobs."""
import json
from typing import Optional, Any
from loguru import logger


def _get_redis():
    """Lazy Redis connection — returns None if Redis is unavailable."""
    try:
        import redis
        from app.config import settings
        r = redis.from_url(settings.redis_url, decode_responses=True, socket_timeout=2)
        r.ping()
        return r
    except Exception as e:
        logger.warning(f"Redis unavailable, queue disabled: {e}")
        return None


def enqueue_job(queue_name: str, payload: dict) -> bool:
    """Push a JSON payload onto a Redis list (LPUSH)."""
    r = _get_redis()
    if not r:
        return False
    try:
        r.lpush(queue_name, json.dumps(payload))
        return True
    except Exception as e:
        logger.error(f"enqueue_job failed: {e}")
        return False


def dequeue_job(queue_name: str, timeout: int = 5) -> Optional[dict]:
    """Block-pop a job from a Redis list (BRPOP)."""
    r = _get_redis()
    if not r:
        return None
    try:
        result = r.brpop(queue_name, timeout=timeout)
        if result:
            _, raw = result
            return json.loads(raw)
    except Exception as e:
        logger.error(f"dequeue_job failed: {e}")
    return None


def set_job_status(job_id: int, status: dict, ttl: int = 86400) -> None:
    """Store job status dict in Redis with a TTL (default 24h)."""
    r = _get_redis()
    if not r:
        return
    try:
        r.setex(f"job_status:{job_id}", ttl, json.dumps(status))
    except Exception as e:
        logger.error(f"set_job_status failed: {e}")


def get_job_status(job_id: int) -> Optional[dict]:
    """Read cached job status from Redis."""
    r = _get_redis()
    if not r:
        return None
    try:
        raw = r.get(f"job_status:{job_id}")
        return json.loads(raw) if raw else None
    except Exception as e:
        logger.error(f"get_job_status failed: {e}")
        return None


def queue_length(queue_name: str) -> int:
    """Return the current length of a Redis queue."""
    r = _get_redis()
    if not r:
        return 0
    try:
        return r.llen(queue_name)
    except Exception:
        return 0
