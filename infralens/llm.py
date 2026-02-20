from __future__ import annotations

import os
from typing import Iterable

from infralens.rules import Finding, RecommendationResult

DEFAULT_MODELS: dict[str, list[str]] = {
    "openai": [
        "gpt-5",
        "gpt-5-mini",
        "gpt-5-nano",
        "chatgpt-4o-latest",
        "gpt-4o-mini",
        "gpt-4o",
        "gpt-4.1-mini",
        "gpt-4.1",
        "o4-mini",
    ],
    "anthropic": [
        "claude-3-7-sonnet-latest",
        "claude-3-5-sonnet-latest",
        "claude-3-5-haiku-latest",
    ],
    "google": [
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-1.5-pro",
    ],
}


def _normalize_provider(provider: str | None) -> str:
    p = (provider or "openai").strip().lower()
    if p in {"openai", "anthropic", "google"}:
        return p
    return "openai"


def _api_key_env(provider: str) -> str:
    if provider == "anthropic":
        return "ANTHROPIC_API_KEY"
    if provider == "google":
        return "GOOGLE_API_KEY"
    return "OPENAI_API_KEY"


def _default_model(provider: str) -> str:
    return DEFAULT_MODELS.get(provider, DEFAULT_MODELS["openai"])[0]


def list_provider_models(provider: str, api_key: str | None) -> tuple[list[str], str | None]:
    p = _normalize_provider(provider)
    defaults = DEFAULT_MODELS[p]
    effective_api_key = (api_key or "").strip() or os.getenv(_api_key_env(p))

    if not effective_api_key:
        return defaults, "missing_api_key"

    try:
        if p == "openai":
            from openai import OpenAI

            client = OpenAI(api_key=effective_api_key)
            response = client.models.list()
            ids: list[str] = []
            try:
                for m in response.auto_paging_iter():
                    mid = getattr(m, "id", None)
                    if isinstance(mid, str):
                        ids.append(mid)
            except Exception:
                ids = [m.id for m in response.data if isinstance(getattr(m, "id", None), str)]
            candidate_ids = sorted(
                {
                    m
                    for m in ids
                    if m.startswith("gpt-")
                    or m.startswith("chatgpt-")
                    or m.startswith("o1")
                    or m.startswith("o3")
                    or m.startswith("o4")
                    or m.startswith("o5")
                }
            )
        elif p == "anthropic":
            from anthropic import Anthropic

            client = Anthropic(api_key=effective_api_key)
            response = client.models.list()
            candidate_ids = sorted({m.id for m in response.data if isinstance(getattr(m, "id", None), str)})
        else:
            import google.generativeai as genai

            genai.configure(api_key=effective_api_key)
            models = genai.list_models()
            candidate_ids = sorted(
                {
                    m.name.split("models/")[-1]
                    for m in models
                    if hasattr(m, "supported_generation_methods")
                    and "generateContent" in (m.supported_generation_methods or [])
                    and isinstance(getattr(m, "name", None), str)
                }
            )

        if not candidate_ids:
            return defaults, "no_text_models_found"

        preferred = [m for m in defaults if m in candidate_ids]
        remaining = [m for m in candidate_ids if m not in preferred]
        return preferred + remaining, None
    except Exception:
        return defaults, "fetch_failed"


def _lang_spec(language: str) -> tuple[str, str]:
    normalized = language.lower()
    if normalized.startswith("ko"):
        return "Korean", "한국어"
    if normalized.startswith("zh"):
        return "Chinese (Simplified)", "中文简体"
    return "English", "English"


def _fallback_analysis_text(
    findings: Iterable[Finding], score: int, grade: str, language: str
) -> str:
    if language.startswith("ko"):
        lines = [f"현재 효율 점수는 {score}/100 ({grade} 등급)입니다.", "주요 병목 요인:"]
    elif language.startswith("zh"):
        lines = [f"当前效率分数为 {score}/100（{grade} 级）。", "主要瓶颈项："]
    else:
        lines = [f"Current efficiency is {score}/100 ({grade} grade).", "Primary bottlenecks identified:"]
    for f in findings:
        lines.append(f"- [{f.category}] {f.message}")
    if language.startswith("ko"):
        lines.append("권장 조치: NUMA 정합성부터 맞춘 뒤, 학습은 NVLink 로컬 그룹에 배치하고 추론은 MIG로 분할하세요.")
    elif language.startswith("zh"):
        lines.append("建议操作：先修正 NUMA 对齐，再将训练任务收敛到同一 NVLink 组，推理任务采用 MIG 切分。")
    else:
        lines.append(
            "Suggested action: prioritize NUMA alignment first, then pack training into NVLink-local GPU groups and split inference via MIG."
        )
    return "\n".join(lines)


def _fallback_recommendation_text(rec: RecommendationResult, language: str) -> str:
    if language.startswith("ko"):
        lines = ["권장 배치안:"]
    elif language.startswith("zh"):
        lines = ["推荐部署方案："]
    else:
        lines = ["Recommended placement plan:"]
    for i, item in enumerate(rec.items, 1):
        lines.append(f"{i}. {item.workload}: {item.action}")
    if language.startswith("ko"):
        lines.append(
            f"예상 효과: GPU 활용률 {rec.expected_util_before}% -> {rec.expected_util_after}%, "
            f"학습 처리량 +{rec.expected_training_gain_pct}%, 추론 레이턴시 -{rec.expected_latency_drop_pct}%."
        )
    elif language.startswith("zh"):
        lines.append(
            f"预期效果：GPU 利用率 {rec.expected_util_before}% -> {rec.expected_util_after}%，"
            f"训练吞吐 +{rec.expected_training_gain_pct}%，推理时延 -{rec.expected_latency_drop_pct}%。"
        )
    else:
        lines.append(
            f"Expected impact: GPU utilization {rec.expected_util_before}% -> {rec.expected_util_after}%, "
            f"training throughput +{rec.expected_training_gain_pct}%, inference latency -{rec.expected_latency_drop_pct}%."
        )
    return "\n".join(lines)


def _invoke_model(provider: str, api_key: str, model: str, prompt: str) -> str:
    p = _normalize_provider(provider)

    if p == "openai":
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        response = client.responses.create(model=model, input=prompt, max_output_tokens=700)
        return (response.output_text or "").strip()

    if p == "anthropic":
        from anthropic import Anthropic

        client = Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model,
            max_tokens=700,
            messages=[{"role": "user", "content": prompt}],
        )
        parts: list[str] = []
        for block in response.content:
            txt = getattr(block, "text", None)
            if isinstance(txt, str):
                parts.append(txt)
        return "\n".join(parts).strip()

    import google.generativeai as genai

    genai.configure(api_key=api_key)
    gen_model = genai.GenerativeModel(model)
    response = gen_model.generate_content(prompt)
    text = getattr(response, "text", None)
    return text.strip() if isinstance(text, str) else ""


def generate_bottleneck_analysis(
    findings: list[Finding],
    score: int,
    grade: str,
    language: str = "ko",
    provider: str = "openai",
    api_key: str | None = None,
    model: str | None = None,
) -> tuple[str, str]:
    p = _normalize_provider(provider)
    effective_api_key = (api_key or "").strip() or os.getenv(_api_key_env(p))
    effective_model = (model or "").strip() or _default_model(p)

    fallback_text = _fallback_analysis_text(findings, score, grade, language)
    prompt_language_en, prompt_language_native = _lang_spec(language)

    if not effective_api_key:
        return fallback_text, f"fallback:{p}:missing_api_key"

    try:
        prompt = (
            "You are a GPU infrastructure optimization expert. "
            f"Explain bottlenecks clearly for non-expert infra engineers in {prompt_language_en} ({prompt_language_native}).\n\n"
            f"Efficiency: {score}/100 ({grade})\n"
            + "\n".join([f"- {f.category}: {f.message}" for f in findings])
        )
        text = _invoke_model(p, effective_api_key, effective_model, prompt)
        return (text or fallback_text), p
    except Exception as exc:
        return fallback_text, f"fallback:{p}:{exc.__class__.__name__}"


def _generate_recommendation_narrative(
    rec: RecommendationResult,
    language: str,
    provider: str = "openai",
    api_key: str | None = None,
    model: str | None = None,
) -> tuple[str, str]:
    p = _normalize_provider(provider)
    effective_api_key = (api_key or "").strip() or os.getenv(_api_key_env(p))
    effective_model = (model or "").strip() or _default_model(p)

    fallback_text = _fallback_recommendation_text(rec, language)
    prompt_language_en, prompt_language_native = _lang_spec(language)

    if not effective_api_key:
        return fallback_text, f"fallback:{p}:missing_api_key"

    try:
        bullet_plan = "\n".join([f"- {i.workload}: {i.action}" for i in rec.items])
        prompt = (
            "You are a GPU infra architect. "
            f"Produce concise actionable recommendations in {prompt_language_en} ({prompt_language_native}).\n\n"
            f"Placement candidates:\n{bullet_plan}\n"
            f"Expected util: {rec.expected_util_before}->{rec.expected_util_after}\n"
            f"Expected training gain: +{rec.expected_training_gain_pct}%\n"
            f"Expected latency drop: -{rec.expected_latency_drop_pct}%"
        )
        text = _invoke_model(p, effective_api_key, effective_model, prompt)
        return (text or fallback_text), p
    except Exception as exc:
        return fallback_text, f"fallback:{p}:{exc.__class__.__name__}"


def generate_recommendation_narrative(
    rec: RecommendationResult,
    language: str = "ko",
    provider: str = "openai",
    api_key: str | None = None,
    model: str | None = None,
) -> tuple[str, str]:
    return _generate_recommendation_narrative(
        rec,
        language,
        provider=provider,
        api_key=api_key,
        model=model,
    )
