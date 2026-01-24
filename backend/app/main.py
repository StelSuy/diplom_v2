import logging
import sys

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.routing import Match
from sqlalchemy.exc import OperationalError, ProgrammingError

from app.core.config import settings
from app.api.router import api_router
from app.db.session import SessionLocal
from app.core.seed import seed_demo_data

# Настройка логирования
logging.basicConfig(
    level=logging.INFO if settings.debug else logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    debug=settings.debug,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В production замените на конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    """Инициализация при старте приложения."""
    logger.info(f"Starting {settings.app_name} in {settings.env} mode")
    
    try:
        db = SessionLocal()
        try:
            created = seed_demo_data(db)
            logger.info(f"Seed demo data: {created}")
        finally:
            db.close()
    except (OperationalError, ProgrammingError) as e:
        logger.warning(f"Seed skipped (DB not ready): {e}")
    except Exception as e:
        logger.exception(f"Seed failed but server continues: {e}")
    
    if settings.debug:
        _debug_routes()


def _debug_routes():
    """Вывод всех зарегистрированных маршрутов."""
    logger.info("\n=== REGISTERED ROUTES ===")
    for r in app.routes:
        if hasattr(r, "methods") and hasattr(r, "path"):
            methods = ",".join(sorted(r.methods))
            logger.info(f"{methods:15} {r.path}")
    logger.info("=== END ROUTES ===\n")


# Exception Handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Глобальный обработчик исключений."""
    logger.exception(f"Unhandled exception on {request.method} {request.url.path}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "path": str(request.url.path),
            "method": request.method,
        }
    )


# Request Logging Middleware (только в debug режиме)
if settings.debug:
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        logger.debug(f">>> {request.method} {request.url.path}")
        
        # Логируем заголовки
        ua = request.headers.get("user-agent", "-")
        ct = request.headers.get("content-type", "-")
        logger.debug(f"    User-Agent: {ua}")
        logger.debug(f"    Content-Type: {ct}")

        # Проверяем совпадение маршрутов
        matches = []
        for r in app.router.routes:
            try:
                m, _ = r.matches(
                    {"type": "http", "method": request.method, "path": request.url.path, "headers": []}
                )
                if m == Match.FULL:
                    matches.append((getattr(r, "path", ""), getattr(r, "methods", None)))
            except Exception:
                pass

        if not matches:
            logger.warning(f"    No route match for {request.method} {request.url.path}")
        else:
            logger.debug(f"    Matched routes: {matches}")

        response = await call_next(request)
        logger.debug(f"<<< {response.status_code} {request.url.path}\n")
        return response


# API Routes
app.include_router(api_router, prefix="/api")

# Admin Panel
app.mount("/admin", StaticFiles(directory="app/static", html=True), name="admin")


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "env": settings.env,
        "version": "1.0.0"
    }


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "TimeTracker API",
        "version": "1.0.0",
        "docs": "/docs",
        "admin": "/admin"
    }
