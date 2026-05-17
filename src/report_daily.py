from __future__ import annotations

from pathlib import Path

from .models import RepoItem
from .utils import ROOT, category_counts, format_dt, keyword_counts, now_shanghai, write_json, write_text


def generate_daily_report(repos: list[RepoItem], raw_count: int, date_string: str | None = None) -> tuple[Path, Path]:
    date = date_string or now_shanghai().strftime("%Y-%m-%d")
    md_path = ROOT / "reports" / "daily" / f"{date}.md"
    json_path = ROOT / "reports" / "daily" / f"{date}.json"

    content = render_daily_markdown(repos, raw_count, date)
    write_text(md_path, content)
    write_json(
        json_path,
        {
            "date": date,
            "generated_at": now_shanghai().isoformat(),
            "raw_count": raw_count,
            "selected_count": len(repos),
            "repos": [repo.to_dict() for repo in repos],
        },
    )
    return md_path, json_path


def render_daily_markdown(repos: list[RepoItem], raw_count: int, date: str) -> str:
    generated_at = now_shanghai().strftime("%Y-%m-%d %H:%M:%S Asia/Shanghai")
    categories = category_counts(repos)
    keywords = keyword_counts(repos)
    top = repos[0] if repos else None
    lines: list[str] = [
        f"# GitHub AI 技术热点日报 - {date}",
        "",
        f"生成时间：{generated_at}",
        "",
        "## 今日概览",
        "",
        f"- 收集项目数：{raw_count}",
        f"- 入选项目数：{len(repos)}",
        f"- 覆盖技术方向：{len(categories)}",
        f"- 最高分项目：{top.full_name if top else '无'}",
        "- 数据来源：GitHub Search API",
        "",
        "## 今日 Top 项目",
        "",
    ]

    if not repos:
        lines += ["今日未收集到符合条件的项目。", ""]
    for index, repo in enumerate(repos, 1):
        lines += [
            f"### {index}. {repo.full_name}",
            "",
            f"- 地址：{repo.html_url}",
            f"- Stars: {repo.stargazers_count}",
            f"- Forks: {repo.forks_count}",
            f"- Watchers: {repo.watchers_count}",
            f"- Open Issues: {repo.open_issues_count}",
            f"- Language: {repo.language}",
            f"- License: {repo.license_name}",
            f"- Updated: {format_dt(repo.pushed_at)}",
            f"- Created: {format_dt(repo.created_at)}",
            f"- Categories: {', '.join(repo.categories)}",
            f"- Topics: {', '.join(repo.topics) if repo.topics else '无'}",
            f"- Matched Keywords: {', '.join(repo.matched_keywords) if repo.matched_keywords else '无'}",
            f"- Trend Score: {repo.trend_score:.2f}",
            "",
            "简介：",
            repo.description or "暂无简介。",
            "",
            "为什么值得关注：",
            repo.reason or "该项目近期活跃，值得继续观察。",
            "",
        ]

    lines += [
        "## 技术方向分布",
        "",
        "| 技术方向 | 项目数 |",
        "| --- | ---: |",
    ]
    lines += [f"| {name} | {count} |" for name, count in categories.most_common()]
    if not categories:
        lines.append("| 无 | 0 |")

    lines += [
        "",
        "## 关键词命中统计",
        "",
        "| 关键词 | 命中项目数 |",
        "| --- | ---: |",
    ]
    lines += [f"| {name} | {count} |" for name, count in keywords.most_common(50)]
    if not keywords:
        lines.append("| 无 | 0 |")

    lines += ["", "## 值得持续跟踪", ""]
    if repos:
        for repo in repos[:10]:
            lines.append(f"- [{repo.full_name}]({repo.html_url})：{repo.reason}")
    else:
        lines.append("- 暂无项目。")
    lines.append("")
    return "\n".join(lines)
