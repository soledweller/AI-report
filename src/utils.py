from __future__ import annotations

import json
import logging
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable
from zoneinfo import ZoneInfo

import yaml
from dateutil import parser

from .models import RepoItem

TZ = ZoneInfo("Asia/Shanghai")
ROOT = Path(__file__).resolve().parent.parent


def setup_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def now_shanghai() -> datetime:
    return datetime.now(TZ)


def today_string() -> str:
    return now_shanghai().strftime("%Y-%m-%d")


def week_string(date: datetime | None = None) -> str:
    d = date or now_shanghai()
    year, week, _ = d.isocalendar()
    return f"{year}-{week:02d}"


def format_dt(value: str) -> str:
    if not value:
        return "Unknown"
    try:
        return parser.isoparse(value).astimezone(TZ).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return value


def parse_dt(value: str) -> datetime:
    if not value:
        return datetime(1970, 1, 1, tzinfo=timezone.utc)
    return parser.isoparse(value)


def cutoff_date(days: int) -> str:
    return (now_shanghai() - timedelta(days=days)).strftime("%Y-%m-%d")


def ensure_dirs() -> None:
    for path in [ROOT / "reports/daily", ROOT / "reports/weekly"]:
        path.mkdir(parents=True, exist_ok=True)


def load_keywords(path: Path | None = None) -> dict[str, list[str]]:
    keyword_path = path or ROOT / "config/keywords.yml"
    with keyword_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return {str(k): [str(x) for x in v or []] for k, v in data.items()}


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dedupe_repos(items: Iterable[RepoItem]) -> list[RepoItem]:
    repos: dict[str, RepoItem] = {}
    for item in items:
        existing = repos.get(item.full_name)
        if not existing:
            repos[item.full_name] = item
            continue
        existing.matched_keywords = sorted(set(existing.matched_keywords + item.matched_keywords))
        existing.categories = sorted(set(existing.categories + item.categories))
        if item.trend_score > existing.trend_score:
            existing.trend_score = item.trend_score
            existing.reason = item.reason
    return list(repos.values())


def sort_repos(items: Iterable[RepoItem]) -> list[RepoItem]:
    return sorted(
        items,
        key=lambda r: (r.trend_score, r.stargazers_count, parse_dt(r.pushed_at)),
        reverse=True,
    )


def category_counts(items: Iterable[RepoItem]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for item in items:
        counter.update(item.categories or ["Uncategorized"])
    return counter


def keyword_counts(items: Iterable[RepoItem]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for item in items:
        counter.update(item.matched_keywords)
    return counter
