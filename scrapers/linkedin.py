from typing import List
from models import JobListing
from scrapers.base_scraper import BaseScraper
import time

class LinkedInScraper(BaseScraper):
    def scrape(self, keyword: str, category_id: str, location: str = "", max_pages: int = 1) -> List[JobListing]:
        jobs = []
        # LinkedIn public search page
        url = f"https://www.linkedin.com/jobs/search?keywords={keyword}&location={location}"
        print(f"Scraping LinkedIn for '{keyword}'...")
        
        try:
            time.sleep(2)  # Delay to avoid rapid blocking
            self.page.goto(url, timeout=30000)
            # Handle cookie banner if present
            try:
                self.page.locator("button[action-type='ACCEPT']").click(timeout=3000)
            except:
                pass
        except Exception as e:
            print(f"Failed to navigate to LinkedIn search for {keyword}: {e}")
            return jobs

        # Scroll to load more jobs if needed
        for _ in range(max_pages):
            self.page.keyboard.press("End")
            time.sleep(2)
            
        job_cards = self.page.locator(".base-card, .job-search-card").all()
        
        for card in job_cards:
            try:
                title_loc = card.locator(".base-search-card__title")
                title = title_loc.inner_text().strip() if title_loc.count() > 0 else "Unknown"
                
                company_loc = card.locator(".base-search-card__subtitle")
                company = company_loc.inner_text().strip() if company_loc.count() > 0 else "Unknown"
                
                loc_loc = card.locator(".job-search-card__location")
                loc = loc_loc.inner_text().strip() if loc_loc.count() > 0 else location
                
                link_loc = card.locator(".base-card__full-link")
                apply_link = link_loc.get_attribute("href") if link_loc.count() > 0 else url
                if apply_link and '?' in apply_link:
                    apply_link = apply_link.split('?')[0] # Clean URL

                job = JobListing(
                    title=title,
                    company=company,
                    location=loc,
                    description="Fetching...",
                    applyLink=apply_link,
                    type="full-time",
                    category=category_id,
                    country=location,
                    status="active",
                    source="linkedin",
                )
                jobs.append(job)
            except Exception as e:
                print(f"Error extracting LinkedIn job: {e}")
                
        # Navigate to individual job pages to get full descriptions
        for job in jobs:
            try:
                if job.applyLink.startswith("http") and "linkedin.com/jobs/view" in job.applyLink:
                    self.page.goto(job.applyLink)
                    self.page.wait_for_load_state("domcontentloaded")
                    
                    # Try to expand the description
                    try:
                        self.page.locator("button.show-more-less-html__button").click(timeout=2000)
                    except:
                        pass
                        
                    # Find description using "About the job" or standard classes
                    desc_loc = self.page.locator(".show-more-less-html__markup, .description__text, .jobs-description-content__text")
                    if desc_loc.count() > 0:
                        job.description = desc_loc.first.inner_text().strip()
                    else:
                        job.description = "Description could not be loaded."
            except Exception as e:
                print(f"Could not load full description for LinkedIn job {job.title}: {e}")
                
        return jobs
