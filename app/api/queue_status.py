"""Queue status endpoint — exposes Redis queue depths for the dashboard."""
from fastapi import APIRouter
from app.config import settings
from app.services.queue_service import qlen

router = APIRouter()


@router.get("/", summary="Redis queue depths")
def queue_status():
    try:
        return {
            "discovery": qlen(settings.redis_queue_discovery),
            "scrape":    qlen(settings.redis_queue_scrape),
            "verify":    qlen(settings.redis_queue_verify),
            "score":     qlen(settings.redis_queue_score),
        }
    except Exception as exc:
        return {"error": str(exc)}
