"""
TruthLens X — FastAPI Application Entry Point.

Wires together all routers, middleware, and startup/shutdown lifecycle.
Models are loaded into app.state at startup and accessed via DI.
"""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database import init_db, close_db
from app.middleware.rate_limiter import limiter, rate_limit_exceeded_handler
from app.middleware.logging_middleware import StructuredLoggingMiddleware
from app.ml.model_loader import load_text_model, load_image_model, load_meta_model

# Import routers
from app.auth.router import router as auth_router
from app.users.router import router as users_router
from app.content.router import router as content_router
from app.history.router import router as history_router
from app.admin.router import router as admin_router


# ─── Logging Configuration ───
def setup_logging():
    """Configure structured JSON logging based on environment."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Root logger
    logging.basicConfig(
        level=log_level,
        format='{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
        stream=sys.stdout,
    )

    # Quiet down noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DEBUG else logging.WARNING
    )
    # Silence transformers warnings during inference
    logging.getLogger("transformers").setLevel(logging.ERROR)
    logging.getLogger("tokenizers").setLevel(logging.ERROR)

    # In production, suppress all debug/info from third-party libs
    if settings.ENVIRONMENT == "production":
        logging.getLogger("uvicorn").setLevel(logging.WARNING)
        logging.getLogger("gunicorn").setLevel(logging.WARNING)


# ─── Application Lifecycle ───
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown lifecycle manager.

    Startup:
    1. Configure logging
    2. Initialize database tables
    3. Load ML models into app.state (eager loading)

    Shutdown:
    1. Close database connections
    """
    # STARTUP
    setup_logging()
    logger = logging.getLogger("truthlens.startup")

    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Load ML models (eager — avoids cold-start latency)
    await load_text_model(app.state)
    await load_image_model(app.state)
    await load_meta_model(app.state)
    logger.info("ML models loaded into app.state")

    yield  # Application runs here

    # SHUTDOWN
    await close_db()
    logger.info("Database connections closed. Shutting down.")


# ─── Application Factory ───
_is_prod = settings.ENVIRONMENT == "production"

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Multi-Modal Content Authenticity Engine. "
        "Detects misinformation in text, AI-generated text, and manipulated images. "
        "Provides credibility scores and explainability (SHAP, Grad-CAM)."
    ),
    version=settings.APP_VERSION,
    lifespan=lifespan,
    # Disable Swagger / ReDoc in production
    docs_url=None if _is_prod else "/docs",
    redoc_url=None if _is_prod else "/redoc",
)


# ─── Middleware (order matters: last added = first executed) ───

# 1. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Structured JSON Logging with perf timing
app.add_middleware(StructuredLoggingMiddleware)

# 3. Rate Limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)


# ─── Routers ───
app.include_router(auth_router, prefix=settings.API_PREFIX)
app.include_router(users_router, prefix=settings.API_PREFIX)
app.include_router(content_router, prefix=settings.API_PREFIX)
app.include_router(history_router, prefix=settings.API_PREFIX)

# Admin router only in development mode
if not _is_prod:
    app.include_router(admin_router, prefix=settings.API_PREFIX)


# ─── Health Check ───
@app.get("/health", tags=["System"])
async def health_check():
    """
    Health check endpoint for monitoring.
    Returns model status, version info, and drift stats.
    """
    # Inference service status
    text_inference = getattr(app.state, "text_inference", None)
    text_loaded = text_inference is not None
    text_status = {}
    if text_loaded:
        text_status = {
            "loaded": True,
            "version": text_inference.version,
            "has_baseline": text_inference.has_baseline,
            "has_advanced": text_inference.has_advanced,
        }
    else:
        text_status = {
            "loaded": False,
            "version": getattr(app.state, "text_model_version", None),
        }

    # Drift stats
    drift_monitor = getattr(app.state, "drift_monitor", None)
    drift_stats = drift_monitor.to_dict() if drift_monitor else None

    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "models": {
            "text": text_status,
            "image": {
                "loaded": getattr(app.state, "image_model", None) is not None,
                "version": getattr(app.state, "image_model_version", None),
            },
        },
        "drift": drift_stats,
    }
