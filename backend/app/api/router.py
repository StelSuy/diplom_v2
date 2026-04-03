from fastapi import APIRouter

from app.api.routes import (
    auth, employees, events, schedules, stats,
    terminals, register, manual_events, audit_log,
    users, positions, export, search,
)

api_router = APIRouter()

# Auth
api_router.include_router(auth.router)

# Core resources
api_router.include_router(employees.router)
api_router.include_router(events.router)
api_router.include_router(schedules.router)
api_router.include_router(stats.router)

# Terminal management
api_router.include_router(terminals.router,        prefix="/terminals", tags=["terminals-admin"])
api_router.include_router(terminals.router_public, prefix="/terminal",  tags=["terminal-public"])

# Register (first scan)
api_router.include_router(register.router, prefix="/register", tags=["register"])

# Manual events (admin)
api_router.include_router(manual_events.router)

# Audit log (admin) — persistent DB
api_router.include_router(audit_log.router)

# Users / admin management
api_router.include_router(users.router)

# Positions directory
api_router.include_router(positions.router)

# Export reports (CSV / XLSX)
api_router.include_router(export.router)

# Live search
api_router.include_router(search.router)
