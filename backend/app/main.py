from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.api.router import api_router
from app.db.init_db import init_db

app = FastAPI(title=settings.app_name)

@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(api_router, prefix="/api")

# Статика для админ-панели
app.mount("/admin", StaticFiles(directory="app/static", html=True), name="admin")

@app.get("/health")
def health():
    return {"status": "ok"}
