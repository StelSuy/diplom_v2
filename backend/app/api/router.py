from fastapi import APIRouter

from app.api.routes import auth, employees, events, schedules, stats, terminals, register

api_router = APIRouter()

# Остальные (как было)
api_router.include_router(auth.router)
api_router.include_router(employees.router)

# если эти файлы у тебя есть — оставь, если нет — удали строки
api_router.include_router(events.router)
api_router.include_router(schedules.router)
api_router.include_router(stats.router)

# ✅ ДАСТ: /api/register/first-scan
api_router.include_router(register.router, prefix="/register", tags=["register"])

# admin terminals (если надо)
api_router.include_router(terminals.router, prefix="/terminals", tags=["terminals-admin"])

# ✅ ДАСТ: /api/terminal/secure-scan (+ /api/terminal/register, /api/terminal/scan если они есть)
api_router.include_router(terminals.router_public, prefix="/terminal", tags=["terminal-public"])
