import argparse
import json

from api.services.scraper_service import scraper_service
from exporter import Exporter


def main():
    parser = argparse.ArgumentParser(description="Job Scraping Tool")
    parser.add_argument(
        "--keyword",
        type=str,
        help="Single job keyword to search for (ignored if --categories is used)",
    )
    parser.add_argument(
        "--categories",
        type=str,
        default="categories.json",
        help="Path to JSON file with categories to bulk scrape",
    )
    parser.add_argument(
        "--parent",
        type=str,
        help="Name of parent category to scrape subcategories for (e.g., 'Technology & IT')",
    )
    parser.add_argument("--location", type=str, default="Egypt", help="Location to search in")
    parser.add_argument(
        "--pages", type=int, default=1, help="Number of pages to scrape per category/platform"
    )
    parser.add_argument("--output", type=str, default=None, help="Output JSON filename")
    parser.add_argument(
        "--platforms",
        type=str,
        default="wuzzuf,linkedin",
        help="Comma-separated platforms: wuzzuf,linkedin",
    )

    args = parser.parse_args()

    if not args.output:
        if args.parent:
            safe_name = args.parent.replace(" & ", "_and_").replace(" ", "_").lower()
            args.output = f"{safe_name}_jobs.json"
        else:
            args.output = "jobs_output.json"

    config = {
        "parent": args.parent,
        "keyword": args.keyword,
        "location": args.location,
        "pages": args.pages,
        "platforms": [p.strip() for p in args.platforms.split(",") if p.strip()],
        "categories": [],
    }

    if args.keyword and not args.parent:
        config["keyword"] = args.keyword
    elif args.parent:
        config["parent"] = args.parent

    all_jobs = scraper_service.scrape_for_cli(config)
    Exporter.to_json(all_jobs, args.output)


if __name__ == "__main__":
    main()
