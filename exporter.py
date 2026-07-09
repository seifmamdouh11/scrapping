import pandas as pd
from typing import List, Union
from models import JobListing

COLUMNS_ORDER = [
    "title", "description", "salary", "type", "company",
    "category", "country", "applyLink", "location", "status",
]


class Exporter:
    @staticmethod
    def _to_dataframe(jobs: List[Union[JobListing, dict]]) -> pd.DataFrame:
        rows = [job.to_dict() if hasattr(job, "to_dict") else job for job in jobs]
        df = pd.DataFrame(rows)
        for col in COLUMNS_ORDER:
            if col not in df.columns:
                df[col] = None
        return df[COLUMNS_ORDER]

    @staticmethod
    def to_json(jobs: List[JobListing], filename: str):
        if not jobs:
            print("No jobs to export.")
            return

        df = Exporter._to_dataframe(jobs)
        df.to_json(filename, orient="records", force_ascii=False, indent=4)
        print(f"Successfully exported {len(jobs)} jobs to {filename}")

    @staticmethod
    def to_csv(jobs: List[Union[JobListing, dict]], filename: str = None) -> str:
        if not jobs:
            return ""

        df = Exporter._to_dataframe(jobs)
        if filename:
            df.to_csv(filename, index=False, encoding="utf-8")
            print(f"Successfully exported {len(jobs)} jobs to {filename}")
            return filename
        return df.to_csv(index=False, encoding="utf-8")
