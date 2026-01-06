from pydantic import BaseModel


class EmployeeCreate(BaseModel):
    full_name: str
    nfc_uid: str
    position: str | None = None
    comment: str | None = None


class EmployeeUpdate(BaseModel):
    full_name: str | None = None
    nfc_uid: str | None = None
    is_active: bool | None = None
    position: str | None = None
    comment: str | None = None


class EmployeeOut(BaseModel):
    id: int
    full_name: str
    nfc_uid: str
    is_active: bool
    position: str | None = None
    comment: str | None = None

    class Config:
        from_attributes = True
