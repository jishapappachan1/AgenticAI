"""Mock LLM client for quota-free learning runs."""

import json

from src.llm.base import LLMClient


class MockLLMClient(LLMClient):
    """
    Deterministic stand-in for LLM reasoning.

    Why this exists:
    - Keeps the Observe->Analyze->Reason->Act flow usable when API quota is unavailable.
    - Helps beginners practice the workflow without requiring paid usage.
    """

    model_name = "mock-architecture-reviewer"

    def generate(self, prompt: str) -> str:
        # Output respects the same JSON contract expected from real LLM output.
        payload = {
            "architecture_overview": (
                "This is a mock reasoning result generated due to LLM unavailability. "
                "The repository appears to follow a modular structure with clear entry points."
            ),
            "strengths": [
                "Repository contains recognizable structure and dependency metadata.",
                "Deterministic preprocessing reduces hallucination risk for architecture inference.",
                "Single-agent pipeline keeps the workflow easy to trace and explain.",
            ],
            "risks_smells": [
                "Mock mode does not provide true model-based reasoning; findings are illustrative.",
                "Architecture conclusions are limited to repository-level signals, not deep code semantics.",
            ],
            "recommendations": [
                "Use this output for flow validation, not final architecture decisions.",
                "Switch back to Gemini once quota is available for richer reasoning.",
                "Add small sample repos to compare deterministic signals vs LLM narrative.",
            ],
            "confidence_note": "Low-to-moderate confidence because mock reasoning is enabled.",
        }
        return json.dumps(payload, indent=2)
