import json
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from api.database import SessionLocal
from api.models_db import ScheduledScrape, ScrapeRun
from api.services.scraper_service import scraper_service

scheduler = BackgroundScheduler()


def _run_scheduled_scrape(schedule_id: int):
    db = SessionLocal()
    try:
        schedule = (
            db.query(ScheduledScrape).filter(ScheduledScrape.id == schedule_id).first()
        )
        if not schedule or not schedule.enabled:
            return

        config = json.loads(schedule.config)
        run = ScrapeRun(
            status="queued",
            config=schedule.config,
            progress=json.dumps({"message": f"Scheduled run: {schedule.name}"}),
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        schedule.last_run_at = datetime.utcnow()
        db.commit()

        scraper_service.run_scrape(config, scrape_run_id=run.id)
    except Exception:
        pass
    finally:
        db.close()


def add_schedule_job(db: Session, schedule: ScheduledScrape):
    job_id = f"schedule_{schedule.id}"
    try:
        scheduler.remove_job(job_id)
    except Exception:
        pass

    if schedule.enabled:
        trigger = CronTrigger.from_crontab(schedule.cron_expression)
        scheduler.add_job(
            _run_scheduled_scrape,
            trigger=trigger,
            id=job_id,
            args=[schedule.id],
            replace_existing=True,
        )
        job = scheduler.get_job(job_id)
        if job and job.next_run_time:
            schedule.next_run_at = job.next_run_time.replace(tzinfo=None)
            db.commit()


def remove_schedule_job(schedule_id: int):
    job_id = f"schedule_{schedule_id}"
    try:
        scheduler.remove_job(job_id)
    except Exception:
        pass


def load_schedules(db: Session):
    schedules = db.query(ScheduledScrape).filter(ScheduledScrape.enabled == True).all()
    for schedule in schedules:
        add_schedule_job(db, schedule)


def start_scheduler():
    if not scheduler.running:
        scheduler.start()
        db = SessionLocal()
        try:
            load_schedules(db)
        finally:
            db.close()


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
