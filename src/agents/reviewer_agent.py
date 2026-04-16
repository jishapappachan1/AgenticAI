"""Reviewer agent that synthesizes final architecture report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.agents.base_agent import BaseAgent
from src.models import ArchitectureReview


class ReviewerAgent(BaseAgent):
    """Produces final structured architecture review from evidence."""

    def __init__(self, llm_client, prompt_path: str) -> None:
        super().__init__(name="reviewer_agent", llm_client=llm_client)
        self.prompt_template = Path(prompt_path).read_text(encoding="utf-8")

    def review(
        self,
        evidence: dict[str, Any],
        user_focus: str,
        plan: dict[str, Any],
    ) -> ArchitectureReview:
        prompt = (
            f"{self.prompt_template}\n\n"
            "Additional instructions:\n"
            "1) This is multi-agent evidence gathered via tool-calling.\n"
            "2) Prefer evidence in 'analysis', 'ingestion', and 'key_file_excerpts'.\n"
            "3) If previous memory exists, use it only as supporting context.\n"
            "4) Return STRICT JSON only.\n\n"
            f"User focus: {user_focus or 'No specific focus provided.'}\n"
            f"Planner output:\n{json.dumps(plan, indent=2)}\n\n"
            f"Analyzer evidence:\n{json.dumps(evidence, indent=2)}\n"
        )

        try:
            parsed = self._generate_json(prompt)
            raw = json.dumps(parsed, indent=2)
        except Exception as exc:
            parsed = {
                "architecture_overview": "Reviewer agent failed to parse model output.",
                "strengths": [],
                "risks_smells": [f"Reviewer output format issue: {exc}"],
                "recommendations": [
                    "Retry run and inspect planner/analyzer evidence payload."
                ],
                "confidence_note": "Low confidence due to reviewer output parsing failure.",
            }
            raw = json.dumps(parsed, indent=2)

        return ArchitectureReview(
            architecture_overview=str(parsed.get("architecture_overview", "")).strip(),
            strengths=[str(item) for item in parsed.get("strengths", [])],
            risks_smells=[str(item) for item in parsed.get("risks_smells", [])],
            recommendations=[str(item) for item in parsed.get("recommendations", [])],
            confidence_note=str(parsed.get("confidence_note", "")).strip(),
            raw_llm_output=raw,
            context={
                "repo_summary": {
                    "repo_name": evidence.get("ingestion", {}).get("repo_name", "repo"),
                    "source_type": evidence.get("ingestion", {}).get("source_type", "unknown"),
                    "total_files": evidence.get("analysis", {}).get("total_files", 0),
                    "top_level_directories": evidence.get("analysis", {}).get(
                        "top_level_directories", []
                    ),
                    "detected_languages": evidence.get("analysis", {}).get(
                        "detected_languages", []
                    ),
                    "key_files": list(evidence.get("ingestion", {}).get("key_files", {}).keys()),
                },
                "analysis": evidence.get("analysis", {}),
                "readme_excerpt": evidence.get("ingestion", {}).get("readme_excerpt", ""),
                "user_focus": user_focus or "No specific focus provided.",
                "previous_summary": evidence.get("previous_summary", {}),
            },
        )

