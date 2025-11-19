import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.logs_config import setup_logging
from app.dependencies import verify_api_key
from app.routers import register, attendance, health


# -----------------------------
# Init logger (single instance)
# -----------------------------
logger = setup_logging()


# -----------------------------
# Lifespan
# -----------------------------
_started_once = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _started_once

    if not _started_once:
        _started_once = True
        logger.info("🔥 App startup (warm-up models if needed)")
    else:
        logger.info("⚠ Duplicate reload startup ignored")

    yield

    logger.info("🔻 App shutdown complete")


# -----------------------------
# FastAPI App
# -----------------------------
app = FastAPI(
    title="Photo Attendance System",
    lifespan=lifespan
)


# -----------------------------
# CORS
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------
# Public Routes (NO API key)
# -----------------------------
app.include_router(
    health.router,
    prefix="/api",
    dependencies=[Depends(verify_api_key)]  # health check
)


# -----------------------------
# Protected Admin Routes
# -----------------------------
app.include_router(
    register.router,
    prefix="/api",
    dependencies=[Depends(verify_api_key)]
)

app.include_router(
    attendance.router,
    prefix="/api",
    dependencies=[Depends(verify_api_key)]
)


# -----------------------------
# Serve Frontend
# -----------------------------
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend_dist")

if os.path.exists(FRONTEND_DIR):
    logger.info(f"📁 Serving frontend from: {FRONTEND_DIR}")
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
else:
    logger.warning("⚠ frontend_dist folder NOT FOUND — API only mode")


logger.info("🚀 FastAPI setup complete. Ready to serve requests.")
