from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
from app.api import jobs, leads, ui


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="B2C Leads Pro", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router)
app.include_router(leads.router)
app.include_router(ui.router)

ui_dir = os.path.join(os.path.dirname(__file__), "../ui")
if os.path.isdir(ui_dir):
    app.mount("/static", StaticFiles(directory=ui_dir), name="static")
