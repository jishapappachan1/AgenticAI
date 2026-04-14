"""Shared data models for deterministic and LLM stages."""

from dataclasses import dataclass, asdict, field
from typing import Any


@dataclass
class RepoIngestionResult:
    """Raw repository information gathered in the Observe stage."""

    repo_name: str
    repo_path: str
    source_type: str
    file_paths: list[str]
    key_files: dict[str, str]
    readme_excerpt: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CodebaseMetadata:
    """Deterministic architecture signals produced in the Analyze stage."""

    total_files: int
    extension_counts: dict[str, int]
    detected_languages: list[str]
    top_level_directories: list[str]
    architecture_hints: list[str]
    framework_signals: list[str]
    dependency_files: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ArchitectureReview:
    """Structured reasoning output returned by the agent."""

    architecture_overview: str
    strengths: list[str]
    risks_smells: list[str]
    recommendations: list[str]
    confidence_note: str = ""
    raw_llm_output: str = ""
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
