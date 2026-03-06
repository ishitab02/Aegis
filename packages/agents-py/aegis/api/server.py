"""FastAPI server."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from aegis.api.routes import demo, detect, forensics, health, monitor, sentinel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Start/stop background tasks on server startup/shutdown."""
    from aegis.api.routes.monitor import (
        start_background_monitor,
        stop_background_monitor,
    )

    start_background_monitor()
    yield
    stop_background_monitor()


app = FastAPI(
    title="AEGIS Agent API",
    description="Sentinel orchestration and forensic analysis API",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(detect.router, prefix="/api/v1/detect", tags=["Detection"])
app.include_router(sentinel.router, prefix="/api/v1/sentinel", tags=["Sentinels"])
app.include_router(forensics.router, prefix="/api/v1/forensics", tags=["Forensics"])
app.include_router(health.router, prefix="/api/v1/health", tags=["Health"])
app.include_router(demo.router, prefix="/api/v1/demo", tags=["Demo"])
app.include_router(monitor.router, prefix="/api/v1/monitor", tags=["Monitor"])


@app.get("/")
async def root():
    return {
        "name": "AEGIS Agent API",
        "version": "0.2.0",
        "status": "running",
    }
