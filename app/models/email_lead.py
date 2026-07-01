import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Text, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class EmailLead(Base):
    __tablename__ = "email_leads"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_page_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pages.id")
    )

    # Core
    email: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(256))
    phone: Mapped[str | None] = mapped_column(String(64))
    website: Mapped[str | None] = mapped_column(Text)
    snippet: Mapped[str | None] = mapped_column(Text)  # surrounding text context

    # Location
    location_raw: Mapped[str | None] = mapped_column(String(512))
    city: Mapped[str | None] = mapped_column(String(256))
    region: Mapped[str | None] = mapped_column(String(256))
    country: Mapped[str | None] = mapped_column(String(128))
    country_code: Mapped[str | None] = mapped_column(String(8))
    location_confidence: Mapped[float] = mapped_column(Float, default=0.0)  # 0.0-1.0

    # Scoring
    lead_score: Mapped[float] = mapped_column(Float, default=0.0)  # 0.0-1.0
    is_suppressed: Mapped[bool] = mapped_column(Boolean, default=False)
    suppressed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    suppressed_reason: Mapped[str | None] = mapped_column(String(256))

    # Meta
    source_url: Mapped[str | None] = mapped_column(Text)
    scraped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    source_page: Mapped["Page"] = relationship(back_populates="email_leads")
    verification: Mapped["Verification"] = relationship(
        back_populates="lead", uselist=False
    )
