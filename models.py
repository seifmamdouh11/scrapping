from dataclasses import dataclass
from typing import Optional

@dataclass
class JobListing:
    title: str
    company: str
    location: str
    description: str
    applyLink: str
    salary: Optional[str] = None
    type: Optional[str] = None
    category: Optional[str] = None
    country: Optional[str] = None
    status: Optional[str] = None
    source: Optional[str] = None

    def to_dict(self):
        return {
            "title": self.title,
            "description": self.description,
            "salary": self.salary,
            "type": self.type,
            "company": self.company,
            "category": self.category,
            "country": self.country,
            "applyLink": self.applyLink,
            "location": self.location,
            "status": self.status,
            "source": self.source,
        }
