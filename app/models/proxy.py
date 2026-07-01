import uuid
from datetime import datetime
from sqlalchemy import String, Float, Integer, Boolean, DateTime, func, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Proxy(Base):
    __tablename__ = "proxies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    url: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    provider: Mapped[str | None] = mapped_column(String(128))
    proxy_type: Mapped[str] = mapped_column(
        String(32), default="datacenter"
    )  # datacenter | residential
    country: Mapped[str | None] = mapped_column(String(8))
    city: Mapped[str | None] = mapped_column(String(128))
    sticky_capable: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    health_score: Mapped[float] = mapped_column(Float, default=1.0)  # 0.0 - 1.0
    avg_latency_ms: Mapped[int | None] = mapped_column(Integer)
    recent_failures: Mapped[int] = mapped_column(Integer, default=0)
    cooldown_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    assignments: Mapped[list["ProxyAssignment"]] = relationship(back_populates="proxy")
    events: Mapped[list["ProxyEvent"]] = relationship(back_populates="proxy")


class ProxyAssignment(Base):
    __tablename__ = "proxy_assignments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    proxy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("proxies.id")
    )
    session_id: Mapped[str | None] = mapped_column(String(128))
    mode: Mapped[str] = mapped_column(String(32), default="rotating")  # rotating | sticky
    country_requested: Mapped[str | None] = mapped_column(String(8))
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    success: Mapped[bool | None] = mapped_column(Boolean)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    blocked: Mapped[bool] = mapped_column(Boolean, default=False)

    proxy: Mapped["Proxy"] = relationship(back_populates="assignments")
    pages: Mapped[list["Page"]] = relationship(back_populates="proxy_assignment")


class ProxyEvent(Base):
    __tablename__ = "proxy_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    proxy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("proxies.id")
    )
    event_type: Mapped[str] = mapped_column(
        String(64)
    )  # success | failure | blocked | captcha | timeout
    domain: Mapped[str | None] = mapped_column(String(256))
    status_code: Mapped[int | None] = mapped_column(Integer)
    message: Mapped[str | None] = mapped_column(Text)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    proxy: Mapped["Proxy"] = relationship(back_populates="events")
