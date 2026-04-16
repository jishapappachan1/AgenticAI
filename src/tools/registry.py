"""Tool registry for controlled agent tool-calling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from src.tools.base import ToolResult


ToolCallable = Callable[..., ToolResult]


@dataclass
class ToolDefinition:
    """Registry metadata for an individual tool."""

    name: str
    description: str
    handler: ToolCallable


class ToolRegistry:
    """In-process registry that validates and executes named tools."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, name: str, description: str, handler: ToolCallable) -> None:
        self._tools[name] = ToolDefinition(name=name, description=description, handler=handler)

    def list_tools(self) -> list[dict[str, str]]:
        return [
            {"name": tool.name, "description": tool.description}
            for tool in self._tools.values()
        ]

    def has_tool(self, name: str) -> bool:
        return name in self._tools

    def call(self, name: str, args: dict[str, Any] | None = None) -> ToolResult:
        if name not in self._tools:
            return ToolResult(ok=False, error=f"Unknown tool: {name}")
        args = args or {}
        try:
            return self._tools[name].handler(**args)
        except Exception as exc:  # pylint: disable=broad-except
            return ToolResult(ok=False, error=str(exc))

