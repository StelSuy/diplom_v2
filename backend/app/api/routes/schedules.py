from fastapi import APIRouter, Depends
from app.api.deps import require_admin

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/")
def list_schedules():
    return {"ok": True, "items": []}
