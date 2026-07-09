import json
from pathlib import Path
from typing import Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CATEGORIES_PATH = BASE_DIR / "categories.json"


def load_categories_raw() -> List[dict]:
    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def build_category_tree() -> List[dict]:
    categories = load_categories_raw()
    parents = [c for c in categories if c.get("parent") is None]
    children_by_parent: Dict[str, List[dict]] = {}

    for cat in categories:
        parent = cat.get("parent")
        if parent is not None:
            parent_id = parent["$oid"]
            children_by_parent.setdefault(parent_id, []).append(cat)

    tree = []
    for parent in parents:
        parent_id = parent["_id"]["$oid"]
        tree.append(
            {
                "id": parent_id,
                "name": parent["name"],
                "slug": parent["slug"],
                "children": [
                    {
                        "id": child["_id"]["$oid"],
                        "name": child["name"],
                        "slug": child["slug"],
                    }
                    for child in children_by_parent.get(parent_id, [])
                ],
            }
        )
    return tree


def get_id_to_name_map() -> Dict[str, str]:
    categories = load_categories_raw()
    return {cat["_id"]["$oid"]: cat["name"] for cat in categories}


def resolve_categories_to_scrape(
    categories: Optional[List[str]] = None,
    parent: Optional[str] = None,
    keyword: Optional[str] = None,
) -> List[dict]:
    categories_data = load_categories_raw()
    categories_to_scrape: List[dict] = []

    target_parent_id = None
    if parent:
        for cat in categories_data:
            if cat["name"].lower() == parent.lower():
                target_parent_id = cat["_id"]["$oid"]
                break
        if not target_parent_id:
            raise ValueError(f"Could not find parent category '{parent}'")

    if categories:
        name_to_cat = {cat["name"].lower(): cat for cat in categories_data}
        for name in categories:
            cat = name_to_cat.get(name.lower())
            if cat:
                categories_to_scrape.append(
                    {"name": cat["name"], "id": cat["_id"]["$oid"]}
                )
            else:
                categories_to_scrape.append({"name": name, "id": name})
    elif parent and target_parent_id:
        for cat in categories_data:
            parent_info = cat.get("parent")
            if parent_info and parent_info.get("$oid") == target_parent_id:
                categories_to_scrape.append(
                    {"name": cat["name"], "id": cat["_id"]["$oid"]}
                )
    elif keyword:
        categories_to_scrape.append({"name": keyword, "id": keyword})

    return categories_to_scrape
