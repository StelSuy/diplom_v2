"""
TimeTracker API — application entry point.
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import OperationalError, ProgrammingError

from app.api.router import api_router
from app.api.routes.auth import init_admin_hash
from app.ws.routes import router as ws_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.seed import seed_admin, seed_demo_data
from app.db.session import SessionLocal

setup_logging()
logger = logging.getLogger(__name__)

APP_VERSION = "1.0.0"


# ── Lifespan (replaces deprecated @app.on_event) ──────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────────────────────────
    logger.info(f"Starting {settings.app_name} v{APP_VERSION} [{settings.env}]")

    # Cache admin password hash once (safe for multi-worker deployments)
    init_admin_hash()

    db = SessionLocal()
    try:
        try:
            seed_admin(db)
        except (OperationalError, ProgrammingError) as e:
            logger.warning(f"Could not seed admin (DB not ready?): {e}")
        except Exception:
            logger.exception("Failed to seed admin user")

        try:
            seed_demo_data(db)
        except (OperationalError, ProgrammingError) as e:
            logger.warning(f"Could not seed demo data (DB not ready?): {e}")
        except Exception:
            logger.exception("Failed to seed demo data")
    finally:
        db.close()

    if settings.debug:
        logger.debug("=== Registered Routes ===")
        for route in app.routes:
            if hasattr(route, "methods") and hasattr(route, "path"):
                logger.debug(f"  {','.join(sorted(route.methods)):10} {route.path}")

    yield

    # ── Shutdown ──────────────────────────────────────────────────────────────
    logger.info("Application shutdown")


# ── App factory ───────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    version=APP_VERSION,
    description="TimeTracker — employee attendance tracking via NFC terminals.",
    debug=settings.debug,
    lifespan=lifespan,
    # Disable Swagger/ReDoc in production
    docs_url="/docs"  if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    openapi_url="/openapi.json" if settings.is_development else None,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request logging middleware (dev only) ─────────────────────────────────────
if settings.is_development:
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        logger.debug(f">>> {request.method} {request.url.path}")
        response = await call_next(request)
        logger.debug(f"<<< {response.status_code}")
        return response


# ── Global exception handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(
        f"Unhandled exception: {request.method} {request.url.path} → {exc}"
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "path": str(request.url.path),
        },
    )


# ── System endpoints ──────────────────────────────────────────────────────────
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    favicon_path = Path(__file__).parent.parent / "favicon.ico"
    if favicon_path.exists():
        return FileResponse(favicon_path)
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": "Not found"})


@app.get("/health", tags=["system"], summary="Health check")
async def health_check():
    """Returns application health status. Used by Docker, load balancers, monitoring."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": APP_VERSION,
        "env": settings.env,
    }


@app.get("/", tags=["system"], include_in_schema=False)
async def root():
    data: dict = {
        "app": settings.app_name,
        "version": APP_VERSION,
        "status": "running",
    }
    if settings.is_development:
        data.update({"docs": "/docs", "redoc": "/redoc", "admin": "/admin"})
    return data


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(api_router, prefix="/api")
app.include_router(ws_router)

# ── Static admin panel ────────────────────────────────────────────────────────
_static = Path(__file__).parent / "static"
if _static.exists():
    app.mount("/admin", StaticFiles(directory=str(_static), html=True), name="admin")
    logger.info("Admin panel mounted at /admin")
