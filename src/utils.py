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


CATEGORY_CN: dict[str, str] = {
    "LLM": "大语言模型",
    "Agent": "AI 智能体",
    "RAG": "检索增强生成",
    "Multimodal": "多模态 AI",
    "Vision": "视觉理解",
    "Speech": "语音 AI",
    "Audio": "音频 AI",
    "Video": "视频 AI",
    "Diffusion": "扩散生成模型",
    "Image Generation": "图像生成",
    "AI Coding": "AI 编程",
    "Inference": "模型推理",
    "Serving": "模型服务",
    "Fine-tuning": "模型微调",
    "Quantization": "模型量化",
    "Evaluation": "模型评测",
    "Benchmark": "基准测试",
    "Dataset": "数据集",
    "Data Engineering": "数据工程",
    "Vector Database": "向量数据库",
    "Embedding": "向量嵌入",
    "Knowledge Graph": "知识图谱",
    "MLOps": "机器学习工程化",
    "Workflow": "工作流",
    "Automation": "自动化",
    "Robotics": "机器人",
    "Edge AI": "边缘 AI",
    "On-device AI": "端侧 AI",
    "AI Security": "AI 安全",
    "AI Infra": "AI 基础设施",
    "Prompt Engineering": "提示词工程",
    "Model Compression": "模型压缩",
    "Alignment": "模型对齐",
    "RLHF": "强化学习反馈",
    "Reasoning": "推理能力",
    "Long Context": "长上下文",
    "Memory": "智能体记忆",
    "Tool Use": "工具调用",
}


def chinese_intro(repo: RepoItem) -> str:
    """Create a short Chinese project intro without calling an external LLM."""
    categories = [CATEGORY_CN.get(category, category) for category in repo.categories[:4]]
    category_text = "、".join(categories) if categories else "AI 技术"
    language_text = "" if repo.language in {"", "Unknown"} else f"，主要使用 {repo.language}"
    keyword_text = ""
    if repo.matched_keywords:
        keyword_text = f"，命中关键词包括 {', '.join(repo.matched_keywords[:4])}"

    purpose = infer_project_purpose(repo)
    return f"这是一个面向{category_text}方向的{purpose}{language_text}{keyword_text}。"


def infer_project_purpose(repo: RepoItem) -> str:
    text = " ".join(
        [
            repo.full_name,
            repo.description or "",
            " ".join(repo.topics),
            " ".join(repo.matched_keywords),
            " ".join(repo.categories),
        ]
    ).lower()
    rules = [
        ("AI Coding", "开发者工具或编程助手项目"),
        ("agent", "智能体框架或自动化工具"),
        ("rag", "知识库问答、检索增强生成或文档检索项目"),
        ("retrieval", "知识库问答、检索增强生成或文档检索项目"),
        ("inference", "模型推理、部署或服务化项目"),
        ("serving", "模型推理、部署或服务化项目"),
        ("fine", "模型训练或微调工具"),
        ("lora", "模型训练或微调工具"),
        ("quant", "模型量化、压缩或低成本部署项目"),
        ("benchmark", "模型评测或基准测试项目"),
        ("eval", "模型评测或基准测试项目"),
        ("dataset", "数据集、数据生成或数据处理项目"),
        ("vector", "向量检索、语义搜索或向量数据库项目"),
        ("embedding", "向量检索、语义搜索或向量数据库项目"),
        ("diffusion", "图像或视频生成项目"),
        ("image generation", "图像或视频生成项目"),
        ("video", "视频理解、视频编辑或视频生成项目"),
        ("speech", "语音识别、语音合成或语音交互项目"),
        ("audio", "音频生成、处理或语音交互项目"),
        ("security", "AI 安全、防护或风险评估项目"),
        ("prompt", "提示词工程、上下文管理或交互优化项目"),
        ("workflow", "AI 工作流编排或自动化项目"),
        ("robot", "机器人或具身智能项目"),
        ("edge", "边缘设备、浏览器或端侧 AI 部署项目"),
        ("mlops", "模型部署、监控或工程化平台"),
    ]
    for needle, purpose in rules:
        if needle.lower() in text:
            return purpose
    if "llm" in text or "language model" in text:
        return "大语言模型应用、框架或工具项目"
    return "开源 AI 项目"
