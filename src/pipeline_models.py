"""Models for multi-agent orchestration and execution traces."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.models import ArchitectureReview


@dataclass
class ToolCallRecord:
    """Trace metadata for a single tool call."""

    agent_name: str
    tool_name: str
    args: dict[str, Any]
    status: str
    duration_ms: int
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "tool_name": self.tool_name,
            "args": self.args,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "error": self.error,
        }


@dataclass
class PipelineRunResult:
    """End-to-end output for a multi-agent architecture review run."""

    run_id: str
    review: ArchitectureReview
    plan: dict[str, Any]
    tool_calls: list[ToolCallRecord] = field(default_factory=list)
    previous_memory_used: bool = False
    model_name: str = ""

