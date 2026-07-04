from fastapi import APIRouter
from fastapi.responses import FileResponse
import os

router = APIRouter(tags=["ui"])


@router.get("/", include_in_schema=False)
async def serve_ui():
    return FileResponse(os.path.join(os.path.dirname(__file__), "../../ui/index.html"))
