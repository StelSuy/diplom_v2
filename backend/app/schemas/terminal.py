from pydantic import BaseModel, field_validator
from typing import Optional


class TerminalRegisterRequest(BaseModel):
    uid: str
    full_name: str
    created_by_terminal_id: int

    @field_validator("created_by_terminal_id", mode="before")
    @classmethod
    def cast_terminal_id(cls, v):
        return int(v)


class TerminalRegisterResponse(BaseModel):
    ok: bool
    message: str
    employee_id: Optional[int] = None


class TerminalScanRequest(BaseModel):
    uid: str
    terminal_id: int
    direction: str
    ts: int

    @field_validator("terminal_id", mode="before")
    @classmethod
    def cast_terminal_id(cls, v):
        return int(v)


class TerminalScanResponse(BaseModel):
    ok: bool
    message: str
    employee_id: Optional[int] = None


class TerminalSecureScanRequest(BaseModel):
    employee_uid: str
    terminal_id: int
    direction: str
    ts: int
    challenge_b64: str
    signature_b64: str

    @field_validator("terminal_id", mode="before")
    @classmethod
    def cast_terminal_id_secure(cls, v):
        return int(v)


class TerminalSecureScanResponse(BaseModel):
    ok: bool
    message: str
    employee_id: Optional[int] = None
