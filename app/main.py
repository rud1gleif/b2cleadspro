from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from app.config import settings

app = FastAPI(
    title="B2C Leads Pro",
    description="Location-based email lead generation with proxy rotation and verification.",
    version="0.1.0",
    debug=settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    logger.info("B2C Leads Pro starting up...")


@app.on_event("shutdown")
async def shutdown():
    logger.info("B2C Leads Pro shutting down.")


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}


# Routers will be registered here as phases are added
# from app.api import jobs, leads, locations, proxies
# app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
# app.include_router(leads.router, prefix="/api/leads", tags=["leads"])
# app.include_router(locations.router, prefix="/api/locations", tags=["locations"])
# app.include_router(proxies.router, prefix="/api/proxies", tags=["proxies"])
