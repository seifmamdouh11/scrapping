import math
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from api.database import get_db
from api.models_db import Job
from api.schemas import JobListResponse, JobResponse

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _job_to_response(job: Job) -> JobResponse:
    return JobResponse(
        id=job.id,
        title=job.title,
        description=job.description or "",
        salary=job.salary,
        type=job.type,
        company=job.company,
        category=job.category,
        country=job.country,
        applyLink=job.applyLink,
        location=job.location,
        status=job.status,
        source=job.source,
        scrape_run_id=job.scrape_run_id,
        scraped_at=job.scraped_at,
    )


@router.get("", response_model=JobListResponse)
def list_jobs(
    q: Optional[str] = None,
    source: Optional[str] = None,
    category: Optional[str] = None,
    company: Optional[str] = None,
    location: Optional[str] = None,
    scrape_run_id: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Job)

    if q:
        pattern = f"%{q}%"
        query = query.filter(
            or_(
                Job.title.ilike(pattern),
                Job.description.ilike(pattern),
                Job.company.ilike(pattern),
            )
        )
    if source:
        query = query.filter(Job.source == source)
    if category:
        query = query.filter(Job.category.ilike(f"%{category}%"))
    if company:
        query = query.filter(Job.company.ilike(f"%{company}%"))
    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))
    if scrape_run_id:
        query = query.filter(Job.scrape_run_id == scrape_run_id)
    if date_from:
        query = query.filter(Job.scraped_at >= datetime.fromisoformat(date_from))
    if date_to:
        query = query.filter(Job.scraped_at <= datetime.fromisoformat(date_to))

    total = query.count()
    total_pages = max(1, math.ceil(total / page_size))
    jobs = (
        query.order_by(Job.scraped_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return JobListResponse(
        items=[_job_to_response(j) for j in jobs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return _job_to_response(job)
