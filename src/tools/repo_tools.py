"""Concrete tool implementations used by analyzer agent."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from src.code_analyzer import analyze_codebase
from src.config import Settings
from src.models import RepoIngestionResult
from src.repo_ingestor import ingest_repository
from src.tools.base import ToolResult
from src.tools.registry import ToolRegistry


def build_tool_registry(
    settings: Settings,
    load_previous_summary: Callable[[str], dict[str, Any] | None],
) -> ToolRegistry:
    """Create and return default tools for repository architecture review."""
    registry = ToolRegistry()

    def ingest_repository_tool(repo_input: str) -> ToolResult:
        ingestion = ingest_repository(repo_input=repo_input, settings=settings)
        return ToolResult(ok=True, data={"ingestion": ingestion.to_dict()})

    def analyze_codebase_tool(ingestion: dict[str, Any]) -> ToolResult:
        result = RepoIngestionResult(
            repo_name=ingestion["repo_name"],
            repo_path=ingestion["repo_path"],
            source_type=ingestion["source_type"],
            file_paths=ingestion["file_paths"],
            key_files=ingestion["key_files"],
            readme_excerpt=ingestion.get("readme_excerpt", ""),
        )
        metadata = analyze_codebase(result)
        return ToolResult(ok=True, data={"analysis": metadata.to_dict()})

    def read_key_file_tool(repo_path: str, relative_path: str, max_chars: int = 2000) -> ToolResult:
        path = Path(repo_path) / relative_path
        if not path.exists() or not path.is_file():
            return ToolResult(ok=False, error=f"File not found: {relative_path}")
        content = path.read_text(encoding="utf-8", errors="ignore")[:max_chars]
        return ToolResult(
            ok=True,
            data={"relative_path": relative_path, "content_excerpt": content},
        )

    def load_previous_summary_tool(repo_input: str) -> ToolResult:
        summary = load_previous_summary(repo_input)
        if not summary:
            return ToolResult(ok=True, data={"found": False, "summary": {}})
        return ToolResult(ok=True, data={"found": True, "summary": summary})

    registry.register(
        name="ingest_repository",
        description="Clone/read repository and collect bounded file inventory.",
        handler=ingest_repository_tool,
    )
    registry.register(
        name="analyze_codebase",
        description="Build deterministic architecture metadata from ingestion payload.",
        handler=analyze_codebase_tool,
    )
    registry.register(
        name="read_key_file",
        description="Read excerpt from a specific repository key file.",
        handler=read_key_file_tool,
    )
    registry.register(
        name="load_previous_summary",
        description="Fetch latest persisted summary for a repository input.",
        handler=load_previous_summary_tool,
    )
    return registry

