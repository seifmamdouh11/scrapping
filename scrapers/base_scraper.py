from abc import ABC, abstractmethod
from typing import List
from models import JobListing
from playwright.sync_api import Page

class BaseScraper(ABC):
    def __init__(self, page: Page):
        self.page = page

    @abstractmethod
    def scrape(self, keyword: str, category_id: str, location: str = "", max_pages: int = 1) -> List[JobListing]:
        """Scrape jobs based on keyword and location"""
        pass
