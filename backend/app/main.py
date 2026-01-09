from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.api.router import api_router
from app.db.init_db import init_db

app = FastAPI(title=settings.app_name)

@app.on_event("startup")
def on_startup():
    init_db()

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


from fastapi import Request
from starlette.routing import Match

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
            m, _ = r.matches({"type": "http", "method": request.method, "path": request.url.path, "headers": []})
            if m == Match.FULL:
                matches.append((getattr(r, "path", ""), getattr(r, "methods", None)))
        except Exception:
            pass

    print(f"    FULL route matches: {matches if matches else 'NONE'}")

    response = await call_next(request)
    print(f"<<< OUT {response.status_code} {request.url.path}\n")
    return response
