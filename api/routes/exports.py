import io
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session

from api.database import get_db
from api.models_db import Job
from api.schemas import ImportResponse
from exporter import Exporter

router = APIRouter(tags=["exports"])


def _filtered_jobs_query(
    db: Session,
    q: Optional[str] = None,
    source: Optional[str] = None,
    category: Optional[str] = None,
    company: Optional[str] = None,
    location: Optional[str] = None,
    scrape_run_id: Optional[int] = None,
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
    return query.order_by(Job.scraped_at.desc())


def _jobs_to_dicts(jobs):
    return [
        {
            "title": j.title,
            "description": j.description,
            "salary": j.salary,
            "type": j.type,
            "company": j.company,
            "category": j.category,
            "country": j.country,
            "applyLink": j.applyLink,
            "location": j.location,
            "status": j.status,
        }
        for j in jobs
    ]


@router.get("/exports/csv")
def export_csv(
    q: Optional[str] = None,
    source: Optional[str] = None,
    category: Optional[str] = None,
    company: Optional[str] = None,
    location: Optional[str] = None,
    scrape_run_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    jobs = _filtered_jobs_query(
        db, q, source, category, company, location, scrape_run_id
    ).all()
    csv_content = Exporter.to_csv(_jobs_to_dicts(jobs))
    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=jobs_export.csv"},
    )


@router.get("/exports/json")
def export_json(
    q: Optional[str] = None,
    source: Optional[str] = None,
    category: Optional[str] = None,
    company: Optional[str] = None,
    location: Optional[str] = None,
    scrape_run_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    jobs = _filtered_jobs_query(
        db, q, source, category, company, location, scrape_run_id
    ).all()
    data = _jobs_to_dicts(jobs)
    content = json.dumps(data, ensure_ascii=False, indent=2)
    return StreamingResponse(
        io.StringIO(content),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=jobs_export.json"},
    )


@router.post("/import/csv", response_model=ImportResponse)
async def import_csv(
    file: UploadFile = File(None),
    path: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    imported = 0
    skipped = 0

    if file and file.filename:
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))
    elif path:
        file_path = Path(path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {path}")
        df = pd.read_csv(file_path)
    else:
        default_path = Path(__file__).resolve().parent.parent.parent / "creative_and_design_jobs_final.csv"
        if not default_path.exists():
            raise HTTPException(status_code=400, detail="No file uploaded and default CSV not found")
        df = pd.read_csv(default_path)

    for _, row in df.iterrows():
        apply_link = str(row.get("applyLink", "")).strip()
        if not apply_link or apply_link == "nan":
            skipped += 1
            continue

        existing = db.query(Job).filter(Job.applyLink == apply_link).first()
        job_data = {
            "title": str(row.get("title", "")),
            "description": str(row.get("description", "")) if pd.notna(row.get("description")) else "",
            "salary": str(row.get("salary", "")) if pd.notna(row.get("salary")) else None,
            "type": str(row.get("type", "full-time")) if pd.notna(row.get("type")) else "full-time",
            "company": str(row.get("company", "")) if pd.notna(row.get("company")) else None,
            "category": str(row.get("category", "")) if pd.notna(row.get("category")) else None,
            "country": str(row.get("country", "")) if pd.notna(row.get("country")) else None,
            "applyLink": apply_link,
            "location": str(row.get("location", "")) if pd.notna(row.get("location")) else None,
            "status": str(row.get("status", "active")) if pd.notna(row.get("status")) else "active",
            "source": "import",
            "scraped_at": datetime.utcnow(),
        }

        if existing:
            for key, val in job_data.items():
                setattr(existing, key, val)
            skipped += 1
        else:
            db.add(Job(**job_data))
            imported += 1

    db.commit()
    return ImportResponse(
        imported=imported,
        skipped=skipped,
        message=f"Imported {imported} jobs, skipped/updated {skipped}",
    )
