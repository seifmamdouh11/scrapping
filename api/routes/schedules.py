import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.database import get_db
from api.models_db import ScheduledScrape
from api.schemas import (
    ScheduleCreateRequest,
    ScheduleResponse,
    ScheduleUpdateRequest,
)
from api.services.scheduler_service import add_schedule_job, remove_schedule_job

router = APIRouter(prefix="/schedules", tags=["schedules"])


def _to_response(schedule: ScheduledScrape) -> ScheduleResponse:
    return ScheduleResponse(
        id=schedule.id,
        name=schedule.name,
        enabled=schedule.enabled,
        cron_expression=schedule.cron_expression,
        config=json.loads(schedule.config),
        last_run_at=schedule.last_run_at,
        next_run_at=schedule.next_run_at,
        created_at=schedule.created_at,
    )


@router.get("", response_model=List[ScheduleResponse])
def list_schedules(db: Session = Depends(get_db)):
    schedules = db.query(ScheduledScrape).order_by(ScheduledScrape.created_at.desc()).all()
    return [_to_response(s) for s in schedules]


@router.post("", response_model=ScheduleResponse, status_code=201)
def create_schedule(request: ScheduleCreateRequest, db: Session = Depends(get_db)):
    schedule = ScheduledScrape(
        name=request.name,
        enabled=request.enabled,
        cron_expression=request.cron_expression,
        config=json.dumps(request.config.model_dump()),
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    add_schedule_job(db, schedule)
    return _to_response(schedule)


@router.patch("/{schedule_id}", response_model=ScheduleResponse)
def update_schedule(
    schedule_id: int,
    request: ScheduleUpdateRequest,
    db: Session = Depends(get_db),
):
    schedule = db.query(ScheduledScrape).filter(ScheduledScrape.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    if request.name is not None:
        schedule.name = request.name
    if request.cron_expression is not None:
        schedule.cron_expression = request.cron_expression
    if request.config is not None:
        schedule.config = json.dumps(request.config.model_dump())
    if request.enabled is not None:
        schedule.enabled = request.enabled

    db.commit()
    db.refresh(schedule)

    if schedule.enabled:
        add_schedule_job(db, schedule)
    else:
        remove_schedule_job(schedule.id)

    return _to_response(schedule)


@router.delete("/{schedule_id}", status_code=204)
def delete_schedule(schedule_id: int, db: Session = Depends(get_db)):
    schedule = db.query(ScheduledScrape).filter(ScheduledScrape.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    remove_schedule_job(schedule.id)
    db.delete(schedule)
    db.commit()
