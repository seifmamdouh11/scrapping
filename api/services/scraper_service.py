import json
from datetime import datetime
from typing import Callable, Dict, List, Optional

from playwright.sync_api import sync_playwright
from sqlalchemy.orm import Session

from api.database import SessionLocal
from api.models_db import Job, ScrapeRun
from api.services.category_loader import get_id_to_name_map, resolve_categories_to_scrape
from models import JobListing
from scrapers.linkedin import LinkedInScraper
from scrapers.wuzzuf import WuzzufScraper


class ScraperService:
    def __init__(self):
        self._id_to_name = get_id_to_name_map()

    def _map_category_name(self, category: Optional[str]) -> Optional[str]:
        if not category:
            return category
        return self._id_to_name.get(category, category)

    def _save_job(
        self,
        db: Session,
        job: JobListing,
        scrape_run_id: Optional[int],
        seen_links: set,
    ) -> bool:
        if not job.applyLink or job.applyLink in seen_links:
            return False

        existing = db.query(Job).filter(Job.applyLink == job.applyLink).first()
        category_name = self._map_category_name(job.category)

        if existing:
            existing.title = job.title
            existing.description = job.description
            existing.salary = job.salary
            existing.type = job.type
            existing.company = job.company
            existing.category = category_name
            existing.country = job.country
            existing.location = job.location
            existing.status = job.status or "active"
            existing.source = job.source
            existing.scrape_run_id = scrape_run_id
            existing.scraped_at = datetime.utcnow()
        else:
            db.add(
                Job(
                    title=job.title,
                    description=job.description or "",
                    salary=job.salary,
                    type=job.type,
                    company=job.company,
                    category=category_name,
                    country=job.country,
                    applyLink=job.applyLink,
                    location=job.location,
                    status=job.status or "active",
                    source=job.source,
                    scrape_run_id=scrape_run_id,
                    scraped_at=datetime.utcnow(),
                )
            )

        seen_links.add(job.applyLink)
        return True

    def _update_run(
        self,
        db: Session,
        scrape_run_id: int,
        status: Optional[str] = None,
        progress: Optional[dict] = None,
        jobs_found: Optional[int] = None,
        error_message: Optional[str] = None,
        finished: bool = False,
    ):
        run = db.query(ScrapeRun).filter(ScrapeRun.id == scrape_run_id).first()
        if not run:
            return

        if status:
            run.status = status
        if progress is not None:
            run.progress = json.dumps(progress)
        if jobs_found is not None:
            run.jobs_found = jobs_found
        if error_message is not None:
            run.error_message = error_message
        if status == "running" and not run.started_at:
            run.started_at = datetime.utcnow()
        if finished:
            run.finished_at = datetime.utcnow()
        db.commit()

    def run_scrape(
        self,
        config: dict,
        scrape_run_id: Optional[int] = None,
        on_progress: Optional[Callable[[dict], None]] = None,
    ) -> List[JobListing]:
        db = SessionLocal()
        all_jobs: List[JobListing] = []
        seen_links: set = set()

        try:
            categories_to_scrape = resolve_categories_to_scrape(
                categories=config.get("categories"),
                parent=config.get("parent"),
                keyword=config.get("keyword"),
            )
            if not categories_to_scrape:
                raise ValueError("No categories to scrape. Provide categories, parent, or keyword.")

            location = config.get("location", "Egypt")
            pages = config.get("pages", 1)
            platforms = config.get("platforms", ["wuzzuf", "linkedin"])
            use_wuzzuf = "wuzzuf" in platforms
            use_linkedin = "linkedin" in platforms

            if scrape_run_id:
                self._update_run(
                    db,
                    scrape_run_id,
                    status="running",
                    progress={
                        "current_category": None,
                        "categories_total": len(categories_to_scrape),
                        "categories_done": 0,
                        "jobs_found": 0,
                        "message": "Starting scrape...",
                    },
                )

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    )
                )
                page = context.new_page()
                w_scraper = WuzzufScraper(page)
                l_scraper = LinkedInScraper(page)

                for idx, cat in enumerate(categories_to_scrape):
                    progress = {
                        "current_category": cat["name"],
                        "categories_total": len(categories_to_scrape),
                        "categories_done": idx,
                        "jobs_found": len(all_jobs),
                        "message": f"Scraping {cat['name']}...",
                    }
                    if on_progress:
                        on_progress(progress)
                    if scrape_run_id:
                        self._update_run(db, scrape_run_id, progress=progress)

                    if use_wuzzuf:
                        w_jobs = w_scraper.scrape(
                            cat["name"], cat["name"], location, pages
                        )
                        for job in w_jobs:
                            job.category = cat["name"]
                            if self._save_job(db, job, scrape_run_id, seen_links):
                                all_jobs.append(job)

                    if use_linkedin:
                        l_jobs = l_scraper.scrape(
                            cat["name"], cat["name"], location, pages
                        )
                        for job in l_jobs:
                            job.category = cat["name"]
                            if self._save_job(db, job, scrape_run_id, seen_links):
                                all_jobs.append(job)

                    db.commit()

                browser.close()

            final_progress = {
                "current_category": None,
                "categories_total": len(categories_to_scrape),
                "categories_done": len(categories_to_scrape),
                "jobs_found": len(all_jobs),
                "message": "Scrape completed.",
            }
            if scrape_run_id:
                self._update_run(
                    db,
                    scrape_run_id,
                    status="completed",
                    progress=final_progress,
                    jobs_found=len(all_jobs),
                    finished=True,
                )
            if on_progress:
                on_progress(final_progress)

            return all_jobs

        except Exception as e:
            if scrape_run_id:
                self._update_run(
                    db,
                    scrape_run_id,
                    status="failed",
                    error_message=str(e),
                    finished=True,
                    progress={
                        "message": f"Scrape failed: {e}",
                        "jobs_found": len(all_jobs),
                    },
                )
            raise
        finally:
            db.close()

    def scrape_for_cli(self, config: dict) -> List[JobListing]:
        return self.run_scrape(config, scrape_run_id=None)


scraper_service = ScraperService()
