from __future__ import annotations

import math
from datetime import timedelta

from .models import RepoItem
from .utils import now_shanghai, parse_dt

AI_TOPICS = {
    "artificial-intelligence",
    "ai",
    "machine-learning",
    "deep-learning",
    "llm",
    "rag",
    "agents",
    "inference",
    "generative-ai",
    "diffusion",
    "transformers",
    "computer-vision",
    "nlp",
}


def _log_score(value: int, scale: int) -> float:
    return min(math.log1p(max(value, 0)) / math.log1p(scale), 1.0)


def recency_score(pushed_at: str, days: int = 7) -> float:
    pushed = parse_dt(pushed_at).astimezone(now_shanghai().tzinfo)
    age = max((now_shanghai() - pushed).total_seconds(), 0)
    day = 24 * 3600
    if age <= day:
        return 1.0
    if age >= days * day:
        return 0.2
    return max(0.2, 1.0 - (age - day) / ((days - 1) * day) * 0.8)


def keyword_score(repo: RepoItem) -> float:
    name = repo.full_name.lower()
    description = (repo.description or "").lower()
    topics = " ".join(repo.topics).lower()
    score = 0.0
    for keyword in set(repo.matched_keywords):
        k = keyword.lower()
        if k in name:
            score += 0.30
        if k in topics:
            score += 0.22
        if k in description:
            score += 0.14
    if not repo.description:
        score *= 0.75
    return min(score, 1.0)


def topic_score(repo: RepoItem) -> float:
    if not repo.topics:
        return 0.0
    hits = {topic.lower() for topic in repo.topics} & AI_TOPICS
    return min(0.25 + len(hits) * 0.18, 1.0) if hits else 0.0


def calculate_trend_score(repo: RepoItem, days: int = 7) -> float:
    stars = _log_score(repo.stargazers_count, 100_000)
    forks = _log_score(repo.forks_count, 20_000)
    recency = recency_score(repo.pushed_at, days=days)
    keyword = keyword_score(repo)
    topic = topic_score(repo)
    score = stars * 0.35 + forks * 0.15 + recency * 0.20 + keyword * 0.20 + topic * 0.10
    return round(score * 100, 2)


def is_recent(repo: RepoItem, days: int) -> bool:
    pushed = parse_dt(repo.pushed_at).astimezone(now_shanghai().tzinfo)
    return pushed >= now_shanghai() - timedelta(days=days)
