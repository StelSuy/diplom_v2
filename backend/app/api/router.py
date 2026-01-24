from fastapi import APIRouter

from app.api.routes import auth, employees, events, schedules, stats, terminals, register, manual_events

api_router = APIRouter()

# Authentication
api_router.include_router(auth.router)

# Main resources
api_router.include_router(employees.router)
api_router.include_router(events.router)
api_router.include_router(schedules.router)
api_router.include_router(stats.router)

# Register (first scan)
api_router.include_router(register.router, prefix="/register", tags=["register"])

# Admin terminals management
api_router.include_router(terminals.router, prefix="/terminals", tags=["terminals-admin"])

# Public terminal endpoints (for Android app)
api_router.include_router(terminals.router_public, prefix="/terminal", tags=["terminal-public"])

# Manual events (admin only) - prefix already in manual_events.router
api_router.include_router(manual_events.router)
