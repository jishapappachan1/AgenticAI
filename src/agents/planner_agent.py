"""Planner agent that proposes tool-based execution plans."""

from __future__ import annotations

import json
from typing import Any

from src.agents.base_agent import BaseAgent


class PlannerAgent(BaseAgent):
    """Creates execution plans and initial tool sequence."""

    def __init__(self, llm_client) -> None:
        super().__init__(name="planner_agent", llm_client=llm_client)

    def plan(
        self,
        repo_input: str,
        user_focus: str,
        tool_catalog: list[dict[str, str]],
        previous_summary: dict[str, Any] | None,
    ) -> dict[str, Any]:
        prompt = (
            "You are the Planner Agent in a multi-agent architecture review pipeline.\n"
            "Create a concise, executable plan that uses available tools.\n"
            "Return STRICT JSON using this schema:\n"
            "{\n"
            '  "goal": "string",\n'
            '  "steps": ["string"],\n'
            '  "tool_sequence": [\n'
            '    {"tool": "tool_name", "args": {"arg": "value"}}\n'
            "  ],\n"
            '  "notes": ["string"]\n'
            "}\n\n"
            "Rules:\n"
            "1) Always include ingest_repository first.\n"
            "2) Include analyze_codebase after ingestion.\n"
            "3) Include load_previous_summary if historical context could help.\n"
            "4) Keep tool_sequence short and deterministic.\n\n"
            f"Repo input: {repo_input}\n"
            f"User focus: {user_focus or 'No specific focus provided'}\n"
            f"Previous summary available: {bool(previous_summary)}\n"
            f"Available tools: {json.dumps(tool_catalog, indent=2)}\n"
        )
        try:
            parsed = self._generate_json(prompt)
        except Exception:
            parsed = {}
        return self._normalize_plan(parsed, repo_input=repo_input)

    def _normalize_plan(self, parsed: dict[str, Any], repo_input: str) -> dict[str, Any]:
        default_tool_sequence: list[dict[str, Any]] = [
            {"tool": "load_previous_summary", "args": {"repo_input": repo_input}},
            {"tool": "ingest_repository", "args": {"repo_input": repo_input}},
            {"tool": "analyze_codebase", "args": {}},
        ]
        tool_sequence = parsed.get("tool_sequence", default_tool_sequence)
        if not isinstance(tool_sequence, list):
            tool_sequence = default_tool_sequence

        normalized_steps = parsed.get(
            "steps",
            [
                "Load any previous memory for this repository input.",
                "Ingest repository structure and key files.",
                "Analyze deterministic architecture metadata.",
                "Hand off evidence to reviewer agent.",
            ],
        )
        if not isinstance(normalized_steps, list):
            normalized_steps = []

        return {
            "goal": str(parsed.get("goal", "Generate architecture evidence for reviewer agent.")),
            "steps": [str(step) for step in normalized_steps],
            "tool_sequence": tool_sequence,
            "notes": [str(note) for note in parsed.get("notes", []) if isinstance(note, str)],
        }

