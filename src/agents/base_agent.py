"""Shared utilities for multi-agent reasoning classes."""

from __future__ import annotations

import json
from typing import Any

from src.llm.base import LLMClient


def extract_json_block(text: str) -> dict[str, Any]:
    """Parse JSON from plain text or fenced markdown output."""
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.startswith("json"):
            stripped = stripped[4:].strip()
    try:
        value = json.loads(stripped)
        if isinstance(value, dict):
            return value
    except json.JSONDecodeError:
        pass

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start >= 0 and end > start:
        value = json.loads(stripped[start : end + 1])
        if isinstance(value, dict):
            return value
    raise ValueError("Unable to extract JSON object from model output.")


class BaseAgent:
    """Base class for all reasoning agents."""

    def __init__(self, name: str, llm_client: LLMClient) -> None:
        self.name = name
        self.llm_client = llm_client

    def _generate_json(self, prompt: str) -> dict[str, Any]:
        output = self.llm_client.generate(prompt)
        return extract_json_block(output)

