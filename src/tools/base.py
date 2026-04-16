"""Base contracts for tool execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ToolResult:
    """Standardized return payload for tool calls."""

    ok: bool
    data: dict[str, Any] | None = None
    error: str = ""

