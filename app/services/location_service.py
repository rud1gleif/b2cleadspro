"""Location resolution helpers using a bundled world-cities CSV."""
import csv
import os
from functools import lru_cache
from typing import List, Dict

DATA_PATH = os.path.join(os.path.dirname(__file__), "../../data/world_cities.csv")


@lru_cache(maxsize=1)
def _load_cities() -> List[Dict]:
    rows = []
    if not os.path.exists(DATA_PATH):
        return rows
    with open(DATA_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def list_countries() -> List[Dict]:
    seen = set()
    result = []
    for row in _load_cities():
        cc = row.get("country_code", "").upper()
        if cc and cc not in seen:
            seen.add(cc)
            result.append({"country": row.get("country", ""), "country_code": cc})
    return sorted(result, key=lambda x: x["country"])


def resolve_location(query: str) -> List[Dict]:
    q = query.lower()
    matches = []
    for row in _load_cities():
        if q in row.get("city", "").lower() or q in row.get("country", "").lower():
            matches.append(row)
        if len(matches) >= 20:
            break
    return matches
