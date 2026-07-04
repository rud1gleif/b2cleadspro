from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, func
from app.database import Base


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    source = Column(String(20), nullable=False, index=True)  # gmaps|yelp|yellowpages|angi
    name = Column(Text, nullable=True)
    phone = Column(Text, nullable=True)
    email = Column(Text, nullable=True)
    website = Column(Text, nullable=True)
    address = Column(Text, nullable=True)
    rating = Column(Float, nullable=True)
    category = Column(Text, nullable=True)
    location = Column(Text, nullable=True)
    niche = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
