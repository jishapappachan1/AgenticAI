"""Single-agent orchestration: Observe -> Analyze -> Reason -> Act."""

from __future__ import annotations

import json
from pathlib import Path

from src.code_analyzer import analyze_codebase
from src.config import Settings
from src.llm.base import LLMClient
from src.models import ArchitectureReview
from src.repo_ingestor import ingest_repository


def _load_prompt(prompt_path: str) -> str:
    return Path(prompt_path).read_text(encoding="utf-8")


def _extract_json_block(text: str) -> dict:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.startswith("json"):
            stripped = stripped[4:].strip()

    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start >= 0 and end > start:
            return json.loads(stripped[start : end + 1])
        raise


class ArchitectureAgent:
    """
    Core single-agent workflow.

    Why this exists:
    - Keeps the full agentic loop in one understandable class for beginners.
    - Separates deterministic observation/analysis from probabilistic reasoning.
    """

    def __init__(self, llm_client: LLMClient, settings: Settings, prompt_path: str) -> None:
        self.llm_client = llm_client
        self.settings = settings
        self.prompt_template = _load_prompt(prompt_path)

    def run(self, repo_input: str, user_focus: str = "") -> ArchitectureReview:
        # Observe
        ingestion = ingest_repository(repo_input, self.settings)

        # Analyze
        metadata = analyze_codebase(ingestion)

        # Reason
        structured_payload = {
            "repo_summary": {
                "repo_name": ingestion.repo_name,
                "source_type": ingestion.source_type,
                "total_files": metadata.total_files,
                "top_level_directories": metadata.top_level_directories[:20],
                "detected_languages": metadata.detected_languages,
                "key_files": list(ingestion.key_files.keys()),
            },
            "analysis": metadata.to_dict(),
            "readme_excerpt": ingestion.readme_excerpt,
            "user_focus": user_focus or "No specific focus provided.",
        }

        prompt = (
            f"{self.prompt_template}\n\n"
            "Repository metadata input:\n"
            f"{json.dumps(structured_payload, indent=2)}"
        )
        llm_output = self.llm_client.generate(prompt)

        # Act (normalize into our strict response contract)
        try:
            parsed = _extract_json_block(llm_output)
        except (json.JSONDecodeError, ValueError):
            parsed = {
                "architecture_overview": "Model output was not strict JSON; see raw output.",
                "strengths": [],
                "risks_smells": ["Response format issue reduced analysis confidence."],
                "recommendations": ["Retry run and verify LLM output contract."],
                "confidence_note": "Low confidence due to parsing failure.",
            }

        return ArchitectureReview(
            architecture_overview=parsed.get("architecture_overview", "").strip(),
            strengths=parsed.get("strengths", []),
            risks_smells=parsed.get("risks_smells", []),
            recommendations=parsed.get("recommendations", []),
            confidence_note=parsed.get("confidence_note", "").strip(),
            raw_llm_output=llm_output,
            context=structured_payload,
        )
