from fastapi import APIRouter
from app.api.routes import auth, employees, terminals, events, schedules, stats

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(employees.router, prefix="/employees", tags=["employees"])
api_router.include_router(terminals.router, prefix="/terminals", tags=["terminals"])
api_router.include_router(events.router, prefix="/events", tags=["events"])
api_router.include_router(schedules.router, prefix="/schedules", tags=["schedules"])
api_router.include_router(stats.router, prefix="/stats", tags=["stats"])
