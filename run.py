from __future__ import annotations

import argparse
import logging

from src.collector import collect_repositories
from src.report_daily import generate_daily_report
from src.report_weekly import generate_weekly_report, load_recent_daily_json
from src.utils import ensure_dirs, load_keywords, setup_logging

LOGGER = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate GitHub AI trend daily and weekly reports.")
    parser.add_argument("--mode", choices=["daily", "weekly", "both"], default="daily")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--min-stars", type=int, default=50)
    parser.add_argument("--pages-per-keyword", type=int, default=1)
    return parser.parse_args()


def run_daily(args: argparse.Namespace) -> list:
    keywords = load_keywords()
    repos, raw_count = collect_repositories(
        keywords=keywords,
        days=args.days,
        limit=args.limit,
        min_stars=args.min_stars,
        pages_per_keyword=args.pages_per_keyword,
    )
    md_path, json_path = generate_daily_report(repos, raw_count)
    LOGGER.info("Daily report generated: %s", md_path)
    LOGGER.info("Daily cache generated: %s", json_path)
    return repos


def run_weekly(args: argparse.Namespace, daily_repos: list | None = None) -> None:
    repos = daily_repos or load_recent_daily_json(days=args.days)
    if not repos:
        LOGGER.info("No recent daily JSON found; collecting fresh weekly data from GitHub API.")
        keywords = load_keywords()
        repos, _ = collect_repositories(
            keywords=keywords,
            days=args.days,
            limit=args.limit,
            min_stars=args.min_stars,
            pages_per_keyword=args.pages_per_keyword,
        )
    md_path = generate_weekly_report(repos, days=args.days)
    LOGGER.info("Weekly report generated: %s", md_path)


def main() -> None:
    setup_logging()
    ensure_dirs()
    args = parse_args()
    if args.mode == "daily":
        run_daily(args)
    elif args.mode == "weekly":
        run_weekly(args)
    else:
        run_daily(args)
        run_weekly(args)


if __name__ == "__main__":
    main()
