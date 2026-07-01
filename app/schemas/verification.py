from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class VerificationRead(BaseModel):
    id: int
    email_lead_id: int
    syntax_ok: bool
    mx_ok: bool
    smtp_ok: Optional[bool]
    is_disposable: bool
    is_role_account: bool
    score: int
    checked_at: datetime

    class Config:
        from_attributes = True
