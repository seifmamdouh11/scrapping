from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class CategoryChild(BaseModel):
    id: str
    name: str
    slug: str


class CategoryParent(BaseModel):
    id: str
    name: str
    slug: str
    children: List[CategoryChild] = []


class ScrapeConfig(BaseModel):
    categories: List[str] = Field(default_factory=list)
    parent: Optional[str] = None
    keyword: Optional[str] = None
    location: str = "Egypt"
    pages: int = 1
    platforms: List[str] = Field(default_factory=lambda: ["wuzzuf", "linkedin"])


class ScrapeCreateRequest(BaseModel):
    config: ScrapeConfig


class ScrapeProgress(BaseModel):
    current_category: Optional[str] = None
    categories_total: int = 0
    categories_done: int = 0
    jobs_found: int = 0
    message: Optional[str] = None


class ScrapeRunResponse(BaseModel):
    id: int
    status: str
    config: dict
    progress: ScrapeProgress
    jobs_found: int
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class JobResponse(BaseModel):
    id: int
    title: str
    description: str
    salary: Optional[str] = None
    type: Optional[str] = None
    company: Optional[str] = None
    category: Optional[str] = None
    country: Optional[str] = None
    applyLink: str
    location: Optional[str] = None
    status: Optional[str] = None
    source: Optional[str] = None
    scrape_run_id: Optional[int] = None
    scraped_at: datetime

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    items: List[JobResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ScheduleCreateRequest(BaseModel):
    name: str
    cron_expression: str
    config: ScrapeConfig
    enabled: bool = True


class ScheduleUpdateRequest(BaseModel):
    name: Optional[str] = None
    cron_expression: Optional[str] = None
    config: Optional[ScrapeConfig] = None
    enabled: Optional[bool] = None


class ScheduleResponse(BaseModel):
    id: int
    name: str
    enabled: bool
    cron_expression: str
    config: dict
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ImportResponse(BaseModel):
    imported: int
    skipped: int
    message: str
