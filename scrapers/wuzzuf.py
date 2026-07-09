from typing import List
from models import JobListing
from scrapers.base_scraper import BaseScraper
import time

class WuzzufScraper(BaseScraper):
    def scrape(self, keyword: str, category_id: str, location: str = "", max_pages: int = 1) -> List[JobListing]:
        jobs = []
        for page_num in range(max_pages):
            url = f"https://wuzzuf.net/search/jobs/?a=hpb&q={keyword}&start={page_num}"
            print(f"Scraping Wuzzuf page {page_num + 1} for '{keyword}'...")
            try:
                time.sleep(2) # Delay to avoid rapid blocking
                self.page.goto(url, timeout=30000)
                self.page.wait_for_load_state("networkidle")
            except Exception as e:
                print(f"Failed to navigate to Wuzzuf search for {keyword}: {e}")
                continue
            
            # Wuzzuf job cards usually have an 'h2' tag for the title
            job_cards = self.page.locator("div.css-1gatmva, div.css-pkv5jc").all()
            if not job_cards:
                # Fallback to general job structure
                job_cards = self.page.locator("h2.css-m604qf").all()
                if not job_cards:
                     # Attempt to find by typical link pattern
                     job_cards = self.page.locator("a[href*='/jobs/p/']").all()

            for card in job_cards:
                try:
                    title_el = card.locator("a[href*='/jobs/p/']").first if card.locator("a[href*='/jobs/p/']").count() > 0 else card
                    title = title_el.inner_text().strip()
                    
                    apply_link = title_el.get_attribute("href")
                    if apply_link and not apply_link.startswith("http"):
                        apply_link = "https://wuzzuf.net" + apply_link
                        
                    # Find company
                    company = "Unknown"
                    company_locs = card.locator("a.css-17s97q8, a[href*='/jobs/careers/']").all()
                    if company_locs:
                        company = company_locs[0].inner_text().strip().replace(" -", "")
                        
                    # Find location
                    loc = "Unknown"
                    location_locs = card.locator("span.css-5wys0k").all()
                    if location_locs:
                        loc = location_locs[0].inner_text().strip()
                        
                    # Find description/details
                    desc = "Unknown"
                    desc_locs = card.locator("div.css-y4udm8").all()
                    if desc_locs:
                        desc = desc_locs[0].inner_text().strip()

                    job = JobListing(
                        title=title,
                        company=company,
                        location=loc,
                        description=desc,
                        applyLink=apply_link,
                        type="full-time",
                        category=category_id,
                        country="Egypt",
                        status="active",
                        source="wuzzuf",
                    )
                    jobs.append(job)
                except Exception as e:
                    print(f"Error extracting Wuzzuf job: {e}")
        
        # Navigate to individual job pages to get full descriptions
        for job in jobs:
            try:
                if job.applyLink and job.applyLink.startswith("http"):
                    self.page.goto(job.applyLink)
                    self.page.wait_for_load_state("domcontentloaded")
                    
                    desc_texts = []
                    # Specifically target the content sections for description and requirements
                    sections = self.page.locator("section.css-1t5f0fr, div.css-1t5f0fr, section[class*='css-']").all()
                    
                    for sec in sections:
                        text = sec.inner_text().strip()
                        if "Job Description" in text or "Job Requirements" in text:
                            # Clean it up slightly to remove footer links if captured
                            if "Links\n\nBlog" in text:
                                text = text.split("Links\n\nBlog")[0].strip()
                            desc_texts.append(text)
                            
                    if desc_texts:
                        job.description = "\n\n".join(desc_texts)
                    else:
                        job.description = "Description could not be loaded."
            except Exception as desc_err:
                print(f"Could not load full description for Wuzzuf job {job.title}: {desc_err}")
                
        return jobs
