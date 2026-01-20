import logging

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.routing import Match
from sqlalchemy.exc import OperationalError, ProgrammingError

from app.core.config import settings
from app.api.router import api_router
from app.db.session import get_db  # твій dependency (yield Session)
from app.core.seed import seed_demo_data  # <-- зроби цей файл як я давав раніше

log = logging.getLogger("uvicorn.error")

app = FastAPI(title=settings.app_name)


from app.db.session import SessionLocal
from app.core.seed import seed_demo_data

@app.on_event("startup")
def on_startup():
    try:
        db = SessionLocal()
        try:
            created = seed_demo_data(db)
            log.info(f"Seed demo data: {created}")
        finally:
            db.close()
    except (OperationalError, ProgrammingError) as e:
        log.warning(f"Seed skipped (DB not ready): {e}")
    except Exception as e:
        log.exception(f"Seed failed but server continues: {e}")



# ВАЖНО: весь API сидит под /api
app.include_router(api_router, prefix="/api")

# Админка
app.mount("/admin", StaticFiles(directory="app/static", html=True), name="admin")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.on_event("startup")
def _debug_routes():
    print("\n=== ROUTES (PATHS) ===")
    for r in app.routes:
        if hasattr(r, "methods") and hasattr(r, "path"):
            methods = ",".join(sorted(r.methods))
            print(f"{methods:15} {r.path}")
    print("=== END ROUTES ===\n")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"\n>>> INCOMING {request.method} {request.url.path}")
    ua = request.headers.get("user-agent", "-")
    ct = request.headers.get("content-type", "-")
    print(f"    UA: {ua}")
    print(f"    CT: {ct}")

    # Покажем, есть ли вообще матч по пути/методу
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

    print(f"    FULL route matches: {matches if matches else 'NONE'}")

    response = await call_next(request)
    print(f"<<< OUT {response.status_code} {request.url.path}\n")
    return response
