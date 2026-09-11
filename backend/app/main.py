from pathlib import Path
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.config import settings
from app.database.db import DATABASE_PATH
from app.services.startup import initialize_application


# ============================================================
# INITIALIZE DATABASE + PRODUCTION SAFETY
# ============================================================

initialize_application()


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Agent 66 - Counselling Support Agent",
)

if settings.environment.strip().lower() != "production":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:5173",
            "http://localhost:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(router)

REPO_ROOT = Path(__file__).resolve().parents[2]
STATIC_DIR = Path(
    os.environ.get(
        "FRONTEND_DIST",
        str(REPO_ROOT / "frontend" / "dist"),
    )
)


def _spa_enabled() -> bool:
    return (STATIC_DIR / "index.html").is_file()


# ============================================================
# ROOT
# ============================================================

@app.get("/")
async def root():
    if _spa_enabled():
        return FileResponse(STATIC_DIR / "index.html")

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
    db_path = Path(DATABASE_PATH)
    return {
        "status": "healthy",
        "environment": settings.environment,
        "database_present": db_path.is_file(),
        "storage_path": str(db_path.parent),
    }


# ============================================================
# PRODUCTION SPA (same-origin frontend + API)
# ============================================================

if (STATIC_DIR / "assets").is_dir():
    app.mount(
        "/assets",
        StaticFiles(directory=STATIC_DIR / "assets"),
        name="assets",
    )


@app.get("/{full_path:path}")
async def spa_fallback(full_path: str):
    """
    Serve the React app for client-side routes in production.

    API routes under /api and /health remain handled above.
    """

    if not _spa_enabled():
        raise HTTPException(status_code=404, detail="Not found")

    reserved = {"docs", "redoc", "openapi.json"}
    first = full_path.split("/", 1)[0]
    if first in reserved:
        raise HTTPException(status_code=404, detail="Not found")

    candidate = STATIC_DIR / full_path
    if candidate.is_file():
        return FileResponse(candidate)

    return FileResponse(STATIC_DIR / "index.html")
