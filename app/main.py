from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from app.config import settings
from app.api import locations, jobs, leads, proxies

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

app.include_router(locations.router, prefix="/api/locations", tags=["Locations"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(leads.router, prefix="/api/leads", tags=["Leads"])
app.include_router(proxies.router, prefix="/api/proxies", tags=["Proxies"])


@app.on_event("startup")
async def startup():
    logger.info("B2C Leads Pro v1.0.0 starting up...")


@app.on_event("shutdown")
async def shutdown():
    logger.info("B2C Leads Pro shutting down.")


@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "ok", "version": "1.0.0"}
