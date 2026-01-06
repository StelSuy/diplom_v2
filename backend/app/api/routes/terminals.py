from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.crud import terminal as terminal_crud

router = APIRouter(dependencies=[Depends(require_admin)])


@router.post("/")
def create_terminal(name: str, db: Session = Depends(get_db)):
    existing = terminal_crud.get_by_name(db, name)
    if existing:
        return {"id": existing.id, "name": existing.name, "api_key": existing.api_key}

    term = terminal_crud.create_terminal(db, name=name)
    return {"id": term.id, "name": term.name, "api_key": term.api_key}


@router.post("/{terminal_id}/rotate_key")
def rotate_key(terminal_id: int, db: Session = Depends(get_db)):
    term = terminal_crud.rotate_api_key(db, terminal_id)
    if not term:
        raise HTTPException(status_code=404, detail="Terminal not found")
    return {"id": term.id, "name": term.name, "api_key": term.api_key}
