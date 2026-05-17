from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class RepoItem:
    full_name: str
    html_url: str
    description: str
    stargazers_count: int
    forks_count: int
    watchers_count: int
    open_issues_count: int
    language: str
    license_name: str
    topics: list[str]
    pushed_at: str
    created_at: str
    updated_at: str
    matched_keywords: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    trend_score: float = 0.0
    reason: str = ""

    @classmethod
    def from_github(cls, payload: dict[str, Any], matched_keywords: list[str] | None = None) -> "RepoItem":
        license_info = payload.get("license") or {}
        return cls(
            full_name=payload.get("full_name") or "",
            html_url=payload.get("html_url") or "",
            description=payload.get("description") or "",
            stargazers_count=int(payload.get("stargazers_count") or 0),
            forks_count=int(payload.get("forks_count") or 0),
            watchers_count=int(payload.get("watchers_count") or 0),
            open_issues_count=int(payload.get("open_issues_count") or 0),
            language=payload.get("language") or "Unknown",
            license_name=license_info.get("spdx_id") or license_info.get("name") or "Unknown",
            topics=list(payload.get("topics") or []),
            pushed_at=payload.get("pushed_at") or "",
            created_at=payload.get("created_at") or "",
            updated_at=payload.get("updated_at") or "",
            matched_keywords=sorted(set(matched_keywords or [])),
        )

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RepoItem":
        return cls(**payload)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
