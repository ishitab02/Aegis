"""FastAPI server."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from aegis.api.routes import demo, detect, forensics, health, sentinel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

app = FastAPI(
    title="AEGIS Agent API",
    description="Sentinel orchestration and forensic analysis API",
    version="0.1.0",
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


@app.get("/")
async def root():
    return {
        "name": "AEGIS Agent API",
        "version": "0.1.0",
        "status": "running",
    }
