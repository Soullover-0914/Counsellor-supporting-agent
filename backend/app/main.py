from fastapi import FastAPI

from app.api.routes import router
from app.core.config import settings

from app.database.db import init_db


# ============================================================
# INITIALIZE DATABASE
# ============================================================

init_db()


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Agent 66 - Counselling Support Agent",
)


app.include_router(router)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
async def root():
    return {
        "agent": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "environment": settings.environment,
    }