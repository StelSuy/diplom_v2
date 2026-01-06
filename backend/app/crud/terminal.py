import secrets
from sqlalchemy.orm import Session

from app.models.terminal import Terminal


def generate_api_key() -> str:
    # 32 байта -> ~43 символа base64url, удобно и достаточно
    return secrets.token_urlsafe(32)


def get_by_name(db: Session, name: str) -> Terminal | None:
    return db.query(Terminal).filter(Terminal.name == name).first()


def get_by_api_key(db: Session, api_key: str) -> Terminal | None:
    return db.query(Terminal).filter(Terminal.api_key == api_key).first()


def create_terminal(db: Session, name: str) -> Terminal:
    term = Terminal(name=name, api_key=generate_api_key())
    db.add(term)
    db.commit()
    db.refresh(term)
    return term


def rotate_api_key(db: Session, terminal_id: int) -> Terminal | None:
    term = db.query(Terminal).filter(Terminal.id == terminal_id).first()
    if not term:
        return None
    term.api_key = generate_api_key()
    db.commit()
    db.refresh(term)
    return term
