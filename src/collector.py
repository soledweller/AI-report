from __future__ import annotations

import logging
from collections import defaultdict

from .classifier import classify_repo
from .github_client import GitHubClient
from .models import RepoItem
from .scorer import AI_TOPICS, calculate_trend_score, is_recent
from .utils import cutoff_date, dedupe_repos, sort_repos

LOGGER = logging.getLogger(__name__)


def collect_repositories(
    keywords: dict[str, list[str]],
    days: int = 7,
    limit: int = 50,
    min_stars: int = 50,
    pages_per_keyword: int = 1,
    client: GitHubClient | None = None,
) -> tuple[list[RepoItem], int]:
    github = client or GitHubClient()
    by_repo: dict[str, RepoItem] = {}
    raw_count = 0

    for category, category_keywords in keywords.items():
        for keyword in category_keywords:
            for sort in ["stars", "updated"]:
                for page in range(1, pages_per_keyword + 1):
                    query = build_query(keyword, days=days, min_stars=min_stars)
                    items = github.search_repositories(query=query, sort=sort, page=page)
                    raw_count += len(items)
                    for payload in items:
                        if should_skip(payload):
                            continue
                        repo = RepoItem.from_github(payload, matched_keywords=[keyword])
                        if not is_recent(repo, days):
                            continue
                        existing = by_repo.get(repo.full_name)
                        if existing:
                            existing.matched_keywords = sorted(set(existing.matched_keywords + [keyword]))
                        else:
                            by_repo[repo.full_name] = repo
                    LOGGER.info("Collected %s items for keyword=%r sort=%s page=%s", len(items), keyword, sort, page)

    repos = dedupe_repos(by_repo.values())
    for repo in repos:
        repo.categories = classify_repo(repo, keywords)
        repo.trend_score = calculate_trend_score(repo, days=days)
        repo.reason = build_reason(repo)

    return sort_repos(repos)[:limit], raw_count


def build_query(keyword: str, days: int, min_stars: int) -> str:
    safe_keyword = keyword.strip()
    if " " in safe_keyword:
        safe_keyword = f'"{safe_keyword}"'
    return f"{safe_keyword} pushed:>={cutoff_date(days)} stars:>={min_stars} archived:false fork:false"


def should_skip(payload: dict) -> bool:
    return bool(payload.get("archived")) or bool(payload.get("fork"))


def build_reason(repo: RepoItem) -> str:
    reasons: list[str] = []
    if repo.stargazers_count >= 10_000:
        reasons.append("已有较高社区关注度")
    elif repo.stargazers_count >= 1_000:
        reasons.append("社区关注度正在形成规模")
    else:
        reasons.append("近期活跃且具备早期观察价值")

    if repo.topics:
        topic_hits = sorted(set(repo.topics) & AI_TOPICS)
        if topic_hits:
            reasons.append(f"命中 {', '.join(topic_hits[:4])} 等 AI 相关 topic")
    if repo.matched_keywords:
        reasons.append(f"关键词覆盖 {', '.join(repo.matched_keywords[:5])}")
    if repo.categories:
        reasons.append(f"可归入 {', '.join(repo.categories[:4])} 方向")

    return "；".join(reasons) + "。"


def group_by_category(repos: list[RepoItem]) -> dict[str, list[RepoItem]]:
    grouped: dict[str, list[RepoItem]] = defaultdict(list)
    for repo in repos:
        for category in repo.categories:
            grouped[category].append(repo)
    return dict(grouped)
