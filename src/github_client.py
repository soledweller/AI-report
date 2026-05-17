from __future__ import annotations

import logging
import os
import time
from typing import Any

import requests

LOGGER = logging.getLogger(__name__)
API_URL = "https://api.github.com/search/repositories"


class GitHubClient:
    def __init__(self, token: str | None = None, timeout: int = 30) -> None:
        self.token = token if token is not None else os.getenv("GITHUB_TOKEN", "")
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "github-ai-trends-actions",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def search_repositories(
        self,
        query: str,
        sort: str = "stars",
        order: str = "desc",
        per_page: int = 30,
        page: int = 1,
    ) -> list[dict[str, Any]]:
        params = {"q": query, "sort": sort, "order": order, "per_page": per_page, "page": page}
        for attempt in range(1, 4):
            try:
                response = requests.get(API_URL, headers=self._headers(), params=params, timeout=self.timeout)
                if response.status_code == 403:
                    message = _extract_message(response)
                    if "rate limit" in message.lower():
                        LOGGER.error("GitHub API rate limit exceeded: %s", message)
                    else:
                        LOGGER.warning("GitHub API forbidden: %s", message)
                    return []
                if response.status_code == 422:
                    LOGGER.warning("Skip invalid GitHub query: %s (%s)", query, _extract_message(response))
                    return []
                if response.status_code >= 500:
                    LOGGER.warning("GitHub API server error %s, attempt %s/3", response.status_code, attempt)
                    time.sleep(attempt * 2)
                    continue
                response.raise_for_status()
                return list(response.json().get("items") or [])
            except requests.RequestException as exc:
                LOGGER.warning("GitHub API request failed, attempt %s/3: %s", attempt, exc)
                if attempt < 3:
                    time.sleep(attempt * 2)
        LOGGER.error("GitHub API failed after retries for query: %s", query)
        return []


def _extract_message(response: requests.Response) -> str:
    try:
        return str(response.json().get("message") or response.text)
    except ValueError:
        return response.text
