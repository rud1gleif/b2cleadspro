"""Serves the static admin dashboard."""
from fastapi import APIRouter
from fastapi.responses import FileResponse
import os

router = APIRouter()

UI_DIR = os.path.join(os.path.dirname(__file__), "../../ui")


@router.get("/", include_in_schema=False)
def serve_dashboard():
    return FileResponse(os.path.join(UI_DIR, "index.html"))
