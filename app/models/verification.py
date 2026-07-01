import uuid
from datetime import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey, Boolean, func, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Verification(Base):
    __tablename__ = "verifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("email_leads.id"), unique=True
    )

    # Results
    syntax_valid: Mapped[bool | None] = mapped_column(Boolean)
    dns_valid: Mapped[bool | None] = mapped_column(Boolean)
    mx_valid: Mapped[bool | None] = mapped_column(Boolean)
    smtp_valid: Mapped[bool | None] = mapped_column(Boolean)
    is_disposable: Mapped[bool | None] = mapped_column(Boolean)
    is_role_account: Mapped[bool | None] = mapped_column(Boolean)  # admin@, info@, etc.
    is_catch_all: Mapped[bool | None] = mapped_column(Boolean)
    is_free_provider: Mapped[bool | None] = mapped_column(Boolean)  # gmail, yahoo, etc.

    # Overall
    verdict: Mapped[str | None] = mapped_column(
        String(32)
    )  # safe | risky | invalid | unknown
    confidence: Mapped[float | None] = mapped_column(Float)  # 0.0-1.0
    raw_response: Mapped[str | None] = mapped_column(Text)  # JSON string
    verifier_version: Mapped[str | None] = mapped_column(String(64))

    last_checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    lead: Mapped["EmailLead"] = relationship(back_populates="verification")
