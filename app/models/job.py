import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, func, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class SearchJob(Base):
    __tablename__ = "search_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("locations.id")
    )
    status: Mapped[str] = mapped_column(
        String(32), default="pending"
    )  # pending | running | done | failed | cancelled
    source_types: Mapped[list | None] = mapped_column(
        JSON
    )  # ["directories", "classifieds", "forums", "events"]
    keywords: Mapped[list | None] = mapped_column(JSON)  # optional keyword filters
    proxy_mode: Mapped[str] = mapped_column(
        String(32), default="rotating_residential"
    )  # rotating_datacenter | rotating_residential | sticky_residential
    pages_discovered: Mapped[int] = mapped_column(Integer, default=0)
    pages_scraped: Mapped[int] = mapped_column(Integer, default=0)
    emails_found: Mapped[int] = mapped_column(Integer, default=0)
    emails_verified: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    location: Mapped["Location"] = relationship(back_populates="jobs")
    pages: Mapped[list["Page"]] = relationship(back_populates="job")
