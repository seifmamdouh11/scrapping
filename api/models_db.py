from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from api.database import Base


class ScrapeRun(Base):
    __tablename__ = "scrape_runs"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String(20), default="queued", nullable=False)
    config = Column(Text, nullable=False)
    progress = Column(Text, default="{}")
    jobs_found = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    jobs = relationship("Job", back_populates="scrape_run")


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (UniqueConstraint("applyLink", name="uq_jobs_apply_link"),)

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, default="")
    salary = Column(String(200), nullable=True)
    type = Column(String(50), nullable=True)
    company = Column(String(300), nullable=True)
    category = Column(String(200), nullable=True)
    country = Column(String(100), nullable=True)
    applyLink = Column(String(1000), nullable=False, index=True)
    location = Column(String(300), nullable=True)
    status = Column(String(50), default="active")
    source = Column(String(20), nullable=True)
    scrape_run_id = Column(Integer, ForeignKey("scrape_runs.id"), nullable=True)
    scraped_at = Column(DateTime, default=datetime.utcnow)

    scrape_run = relationship("ScrapeRun", back_populates="jobs")


class ScheduledScrape(Base):
    __tablename__ = "scheduled_scrapes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    enabled = Column(Boolean, default=True)
    cron_expression = Column(String(100), nullable=False)
    config = Column(Text, nullable=False)
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
