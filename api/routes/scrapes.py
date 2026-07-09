import asyncio
import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.database import get_db
from api.models_db import ScrapeRun
from api.schemas import ScrapeCreateRequest, ScrapeProgress, ScrapeRunResponse
from api.services.scraper_service import scraper_service

router = APIRouter(prefix="/scrapes", tags=["scrapes"])


def _parse_run(run: ScrapeRun) -> ScrapeRunResponse:
    config = json.loads(run.config) if run.config else {}
    progress_data = json.loads(run.progress) if run.progress else {}
    progress = ScrapeProgress(**progress_data) if progress_data else ScrapeProgress()
    return ScrapeRunResponse(
        id=run.id,
        status=run.status,
        config=config,
        progress=progress,
        jobs_found=run.jobs_found or 0,
        error_message=run.error_message,
        started_at=run.started_at,
        finished_at=run.finished_at,
        created_at=run.created_at,
    )


def _run_scrape_background(scrape_run_id: int, config: dict):
    scraper_service.run_scrape(config, scrape_run_id=scrape_run_id)


@router.post("", response_model=ScrapeRunResponse, status_code=201)
def start_scrape(
    request: ScrapeCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    config = request.config.model_dump()
    run = ScrapeRun(
        status="queued",
        config=json.dumps(config),
        progress=json.dumps({"message": "Queued", "jobs_found": 0}),
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    background_tasks.add_task(_run_scrape_background, run.id, config)
    return _parse_run(run)


@router.get("", response_model=list[ScrapeRunResponse])
def list_scrapes(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    runs = (
        db.query(ScrapeRun)
        .order_by(ScrapeRun.created_at.desc())
        .limit(limit)
        .all()
    )
    return [_parse_run(r) for r in runs]


@router.get("/{scrape_id}", response_model=ScrapeRunResponse)
def get_scrape(scrape_id: int, db: Session = Depends(get_db)):
    run = db.query(ScrapeRun).filter(ScrapeRun.id == scrape_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Scrape run not found")
    return _parse_run(run)
