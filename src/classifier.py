from __future__ import annotations

from collections import defaultdict

from .models import RepoItem

TAG_RULES: dict[str, list[str]] = {
    "LLM": ["llm", "language model", "foundation model", "transformer", "qwen", "llama", "mistral", "gemma", "deepseek"],
    "Agent": ["agent", "agentic", "autogen", "crewai", "langgraph", "openhands"],
    "RAG": ["rag", "retrieval", "reranker", "document qa"],
    "Multimodal": ["multimodal", "vlm", "vision language"],
    "Vision": ["computer-vision", "vision", "image understanding", "ocr"],
    "Speech": ["speech", "asr", "tts", "whisper"],
    "Audio": ["audio", "music generation", "voice"],
    "Video": ["video", "text to video", "temporal"],
    "Diffusion": ["diffusion", "stable diffusion", "comfyui", "controlnet", "flux"],
    "Image Generation": ["image generation", "text to image", "image editing"],
    "AI Coding": ["coding", "code generation", "copilot", "swe", "code review"],
    "Inference": ["inference", "vllm", "sglang", "llama.cpp", "ollama", "tgi"],
    "Serving": ["serving", "model serving", "openai compatible api"],
    "Fine-tuning": ["fine tuning", "finetuning", "lora", "qlora", "peft", "sft"],
    "Quantization": ["quantization", "int4", "int8", "gguf", "gptq", "awq"],
    "Evaluation": ["evaluation", "eval", "llm judge", "red teaming"],
    "Benchmark": ["benchmark", "leaderboard"],
    "Dataset": ["dataset", "corpus", "synthetic data"],
    "Data Engineering": ["data pipeline", "data cleaning", "data extraction", "web scraping"],
    "Vector Database": ["vector database", "vector db", "milvus", "qdrant", "chroma", "weaviate", "faiss", "pgvector"],
    "Embedding": ["embedding", "semantic search", "similarity search"],
    "Knowledge Graph": ["knowledge graph", "graph rag"],
    "MLOps": ["mlops", "llmops", "observability", "model registry", "experiment tracking"],
    "Workflow": ["workflow", "agentic workflow"],
    "Automation": ["automation", "task automation"],
    "Robotics": ["robot", "robotics", "embodied", "vla"],
    "Edge AI": ["edge ai", "tinyml", "webgpu", "wasm"],
    "On-device AI": ["on device", "mobile inference", "coreml", "npu"],
    "AI Security": ["security", "prompt injection", "jailbreak", "guardrails", "privacy"],
    "AI Infra": ["ai infra", "gpu cluster", "distributed training", "deepspeed", "megatron", "ray", "kubernetes"],
    "Prompt Engineering": ["prompt engineering", "prompt management", "context engineering"],
    "Model Compression": ["model compression", "pruning", "low bit"],
    "Alignment": ["alignment", "preference optimization", "dpo", "grpo"],
    "RLHF": ["rlhf", "reward model"],
    "Reasoning": ["reasoning", "reasoning model"],
    "Long Context": ["long context", "context"],
    "Memory": ["memory", "agent memory"],
    "Tool Use": ["tool calling", "function calling", "computer use"],
}


def classify_repo(repo: RepoItem, keyword_categories: dict[str, list[str]]) -> list[str]:
    labels: set[str] = set()
    keyword_to_category = defaultdict(list)
    for category, keywords in keyword_categories.items():
        for keyword in keywords:
            keyword_to_category[keyword.lower()].append(category)

    for keyword in repo.matched_keywords:
        for category in keyword_to_category[keyword.lower()]:
            labels.add(category)

    haystack = " ".join(
        [
            repo.full_name,
            repo.description or "",
            " ".join(repo.topics or []),
            " ".join(repo.matched_keywords or []),
        ]
    ).lower()

    for label, needles in TAG_RULES.items():
        if any(needle in haystack for needle in needles):
            labels.add(label)

    if "Audio Speech" in labels:
        labels.update({"Audio", "Speech"})
        labels.discard("Audio Speech")
    if "Vector Database" in labels and "Embedding" not in labels and "embedding" in haystack:
        labels.add("Embedding")

    return sorted(labels) or ["AI"]
