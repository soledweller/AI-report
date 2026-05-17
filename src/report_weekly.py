from __future__ import annotations

from collections import Counter, defaultdict
from datetime import timedelta
from pathlib import Path

from .models import RepoItem
from .utils import (
    ROOT,
    category_counts,
    chinese_intro,
    format_dt,
    keyword_counts,
    now_shanghai,
    read_json,
    sort_repos,
    week_string,
    write_json,
    write_text,
)


def load_recent_daily_json(days: int = 7) -> list[RepoItem]:
    daily_dir = ROOT / "reports" / "daily"
    repos: list[RepoItem] = []
    start = now_shanghai().date() - timedelta(days=days - 1)
    for path in sorted(daily_dir.glob("*.json")):
        try:
            report_date = path.stem
            if report_date < start.strftime("%Y-%m-%d"):
                continue
            payload = read_json(path)
            repos.extend(RepoItem.from_dict(item) for item in payload.get("repos", []))
        except Exception:
            continue
    return repos


def generate_weekly_report(repos: list[RepoItem], days: int = 7, date_string: str | None = None) -> Path:
    current = now_shanghai()
    week_id = date_string or week_string(current)
    start = (current.date() - timedelta(days=days - 1)).strftime("%Y-%m-%d")
    end = current.date().strftime("%Y-%m-%d")
    md_path = ROOT / "reports" / "weekly" / f"{week_id}.md"
    json_path = ROOT / "reports" / "weekly" / f"{week_id}.json"

    merged = merge_weekly_repos(repos)
    content = render_weekly_markdown(merged, week_id, start, end)
    write_text(md_path, content)
    write_json(
        json_path,
        {
            "week": week_id,
            "start": start,
            "end": end,
            "generated_at": now_shanghai().isoformat(),
            "repos": [repo.to_dict() for repo in merged],
        },
    )
    return md_path


def merge_weekly_repos(repos: list[RepoItem]) -> list[RepoItem]:
    by_name: dict[str, RepoItem] = {}
    appearances: Counter[str] = Counter()
    for repo in repos:
        appearances[repo.full_name] += 1
        existing = by_name.get(repo.full_name)
        if not existing:
            by_name[repo.full_name] = repo
            continue
        existing.matched_keywords = sorted(set(existing.matched_keywords + repo.matched_keywords))
        existing.categories = sorted(set(existing.categories + repo.categories))
        existing.trend_score = max(existing.trend_score, repo.trend_score)
        if len(repo.reason) > len(existing.reason):
            existing.reason = repo.reason
    for repo in by_name.values():
        if appearances[repo.full_name] > 1:
            repo.trend_score = round(repo.trend_score + min(appearances[repo.full_name], 5), 2)
    return sort_repos(by_name.values())


def render_weekly_markdown(repos: list[RepoItem], week_id: str, start: str, end: str) -> str:
    generated_at = now_shanghai().strftime("%Y-%m-%d %H:%M:%S Asia/Shanghai")
    cats = category_counts(repos)
    keys = keyword_counts(repos)
    grouped: dict[str, list[RepoItem]] = defaultdict(list)
    for repo in repos:
        for category in repo.categories:
            grouped[category].append(repo)

    lines = [
        f"# GitHub AI 技术趋势周报 - {week_id}",
        "",
        f"统计周期：{start} 至 {end}",
        f"生成时间：{generated_at}",
        "",
        "## 本周总结",
        "",
        build_summary(repos, cats, keys),
        "",
        "## 本周 Top 20 项目",
        "",
        "| 排名 | 项目 | 分类 | Stars | Forks | Score | 最近更新 |",
        "| ---: | --- | --- | ---: | ---: | ---: | --- |",
    ]
    if repos:
        for index, repo in enumerate(repos[:20], 1):
            lines.append(
                f"| {index} | [{repo.full_name}]({repo.html_url}) | {', '.join(repo.categories[:4])} | "
                f"{repo.stargazers_count} | {repo.forks_count} | {repo.trend_score:.2f} | {format_dt(repo.pushed_at)} |"
            )
    else:
        lines.append("| - | 无 | 无 | 0 | 0 | 0 | - |")

    lines += ["", "## 按技术方向归类", ""]
    if grouped:
        for category, items in sorted(grouped.items(), key=lambda kv: (-len(kv[1]), kv[0])):
            lines += [f"### {category}", ""]
            for repo in sort_repos(items)[:8]:
                lines.append(f"- [{repo.full_name}]({repo.html_url})：{chinese_intro(repo)}Score {repo.trend_score:.2f}。")
            lines.append("")
    else:
        lines.append("暂无可归类项目。")
        lines.append("")

    lines += [
        "## 本周关键词趋势",
        "",
        "| 关键词 | 命中次数 |",
        "| --- | ---: |",
    ]
    lines += [f"| {keyword} | {count} |" for keyword, count in keys.most_common(50)]
    if not keys:
        lines.append("| 无 | 0 |")

    lines += ["", "## 持续升温项目", ""]
    hot = [repo for repo in repos if repo.trend_score >= 70 or repo.stargazers_count >= 5_000][:10]
    if hot:
        for repo in hot:
            lines.append(f"- [{repo.full_name}]({repo.html_url})：{chinese_intro(repo)}{repo.reason}")
    else:
        lines.append("- 暂无明显持续升温项目。")

    lines += ["", "## 值得长期关注", ""]
    if repos:
        for repo in repos[:10]:
            lines.append(f"- [{repo.full_name}]({repo.html_url})：{chinese_intro(repo)}{long_term_reason(repo)}")
    else:
        lines.append("- 暂无项目。")
    lines.append("")
    return "\n".join(lines)


def build_summary(repos: list[RepoItem], cats: Counter[str], keys: Counter[str]) -> str:
    if not repos:
        return "最近 7 天没有可用日报数据，且本次未收集到符合条件的项目。"
    top_categories = "、".join(name for name, _ in cats.most_common(5)) or "暂无"
    top_keywords = "、".join(name for name, _ in keys.most_common(8)) or "暂无"
    leader = repos[0]
    return (
        f"本周共汇总 {len(repos)} 个去重项目，热点主要集中在 {top_categories} 等方向。"
        f"关键词上，{top_keywords} 的出现频率较高。"
        f"综合评分最高的是 {leader.full_name}，说明近期 GitHub AI 生态仍围绕模型能力、工程落地和开发者工具持续推进。"
    )


def long_term_reason(repo: RepoItem) -> str:
    parts = [f"综合分 {repo.trend_score:.2f}"]
    if repo.stargazers_count:
        parts.append(f"Stars {repo.stargazers_count}")
    if repo.categories:
        parts.append(f"覆盖 {', '.join(repo.categories[:3])}")
    if repo.matched_keywords:
        parts.append(f"关键词 {', '.join(repo.matched_keywords[:3])}")
    return "，".join(parts) + "，适合纳入后续趋势观察。"
