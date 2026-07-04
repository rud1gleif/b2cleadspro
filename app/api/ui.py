"""Serves the single-page frontend."""
import pathlib
from fastapi import APIRouter
from fastapi.responses import Response

router = APIRouter()

_HTML_PATH = pathlib.Path(__file__).parent / "static" / "index.html"

@router.get("/", response_class=Response)
async def index():
    html = _HTML_PATH.read_text(encoding="utf-8")
    return Response(content=html.encode("utf-8"), media_type="text/html; charset=utf-8")
