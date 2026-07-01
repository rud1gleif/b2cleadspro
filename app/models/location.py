import uuid
from datetime import datetime
from sqlalchemy import String, Float, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    raw_input: Mapped[str] = mapped_column(String(512), nullable=False)
    city: Mapped[str | None] = mapped_column(String(256))
    region: Mapped[str | None] = mapped_column(String(256))
    country: Mapped[str | None] = mapped_column(String(128))
    country_code: Mapped[str | None] = mapped_column(String(8))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    population: Mapped[int | None] = mapped_column()
    timezone: Mapped[str | None] = mapped_column(String(64))
    normalized: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    jobs: Mapped[list["SearchJob"]] = relationship(back_populates="location")

    def __repr__(self) -> str:
        return f"<Location {self.city}, {self.country_code}>"
