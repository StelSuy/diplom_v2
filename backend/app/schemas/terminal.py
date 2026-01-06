from pydantic import BaseModel


class TerminalCreate(BaseModel):
    name: str


class TerminalOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True
