from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    locations = Column(Text, nullable=False)          # JSON array as string: '["Miami","Dallas"]'
    niches = Column(Text, nullable=True)              # CSV: "plumber,roofer"
    sources = Column(Text, nullable=False, default="gmaps,yelp,yellowpages,angi")
    max_pages = Column(Integer, nullable=False, default=5)
    concurrency = Column(Integer, nullable=False, default=3)
    status = Column(String(20), nullable=False, default="pending")  # pending|running|done|error
    leads_found = Column(Integer, nullable=False, default=0)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
