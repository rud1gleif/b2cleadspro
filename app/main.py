from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger
import os
from app.config import settings
from app.api import locations, jobs, leads, proxies
from app.api.stats import router as stats_router
from app.api.verify import router as verify_router
from app.api.ui import router as ui_router
from app.services.disposable_service import refresh_disposable_list, start_auto_refresh

app = FastAPI(
    title="B2C Leads Pro",
    description="Location-based B2C email lead generation with proxy rotation and verification.",
    version="1.0.0",
    debug=settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(locations.router, prefix="/api/locations",  tags=["Locations"])
app.include_router(jobs.router,      prefix="/api/jobs",       tags=["Jobs"])
app.include_router(leads.router,     prefix="/api/leads",      tags=["Leads"])
app.include_router(proxies.router,   prefix="/api/proxies",    tags=["Proxies"])
app.include_router(stats_router,     prefix="/api/stats",      tags=["Stats"])
app.include_router(verify_router,    prefix="/api/verify",     tags=["Verification"])

# Serve static UI assets
UI_DIR = os.path.join(os.path.dirname(__file__), "../ui")
if os.path.isdir(os.path.join(UI_DIR, "static")):
    app.mount("/static", StaticFiles(directory=os.path.join(UI_DIR, "static")), name="static")

# Dashboard root (must come last)
app.include_router(ui_router, prefix="", tags=["Dashboard"])


@app.on_event("startup")
async def startup():
    logger.info("B2C Leads Pro v1.0.0 starting up...")
    # Load disposable-domain blocklist in background and start 24h auto-refresh
    import threading
    threading.Thread(
        target=refresh_disposable_list, daemon=True, name="disposable-init"
    ).start()
    start_auto_refresh()


@app.on_event("shutdown")
async def shutdown():
    logger.info("B2C Leads Pro shutting down.")


@app.get("/health", tags=["System"])
async def health_check():
    from app.services.disposable_service import disposable_domain_count
    return {
        "status": "ok",
        "version": "1.0.0",
        "disposable_domains_loaded": disposable_domain_count(),
    }
