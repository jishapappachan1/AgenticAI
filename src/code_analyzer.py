"""Deterministic codebase analysis for the Analyze stage."""

from __future__ import annotations

from collections import Counter
from pathlib import PurePosixPath

from src.models import CodebaseMetadata, RepoIngestionResult


EXTENSION_TO_LANGUAGE = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".go": "Go",
    ".rb": "Ruby",
    ".cs": "C#",
    ".php": "PHP",
    ".rs": "Rust",
}


def _detect_framework_signals(file_paths: list[str]) -> list[str]:
    signals: list[str] = []
    lower_files = {path.lower() for path in file_paths}

    if "requirements.txt" in lower_files or "pyproject.toml" in lower_files:
        signals.append("Python dependency management detected")
    if "package.json" in lower_files:
        signals.append("Node.js ecosystem detected")
    if "dockerfile" in lower_files or "docker-compose.yml" in lower_files:
        signals.append("Containerization setup detected")
    if any(path.startswith(".github/workflows/") for path in lower_files):
        signals.append("GitHub Actions CI workflows detected")

    return signals


def _detect_architecture_hints(top_level_dirs: list[str], file_paths: list[str]) -> list[str]:
    hints: list[str] = []
    dirs = {d.lower() for d in top_level_dirs}
    lower_paths = [path.lower() for path in file_paths]

    if any(name in dirs for name in {"api", "backend", "server", "services"}):
        hints.append("Backend or service-oriented structure is present")
    if any(name in dirs for name in {"frontend", "ui", "web", "client"}):
        hints.append("Separate frontend or UI layer is present")
    if any(name in dirs for name in {"db", "database", "migrations", "models"}):
        hints.append("Data and persistence concerns are explicitly modeled")
    if any("/tests/" in f or f.startswith("tests/") for f in lower_paths):
        hints.append("Automated test layout is present")
    if any(path.endswith(("routes.py", "router.py", "urls.py")) for path in lower_paths):
        hints.append("Routing layer appears to be explicitly defined")

    return hints


def analyze_codebase(ingestion: RepoIngestionResult) -> CodebaseMetadata:
    """
    Build deterministic architecture metadata from repository shape.

    Why this exists:
    - Keeps the reasoning stage grounded in factual repository signals.
    - Avoids expensive static analysis for a beginner-friendly MVP.
    """
    file_paths = ingestion.file_paths
    ext_counts: Counter[str] = Counter()
    top_level_dirs: set[str] = set()
    dependency_files: list[str] = []

    dependency_candidates = {
        "requirements.txt",
        "pyproject.toml",
        "package.json",
        "pom.xml",
        "build.gradle",
        "go.mod",
        "cargo.toml",
    }

    for file_path in file_paths:
        path = PurePosixPath(file_path)
        ext = path.suffix.lower() or "<no_ext>"
        ext_counts[ext] += 1
        # Only include real top-level directories, not root-level files.
        if len(path.parts) > 1:
            top_level_dirs.add(path.parts[0])
        if file_path.lower() in dependency_candidates:
            dependency_files.append(file_path)

    detected_languages = sorted(
        {
            EXTENSION_TO_LANGUAGE[ext]
            for ext in ext_counts
            if ext in EXTENSION_TO_LANGUAGE
        }
    )
    sorted_dirs = sorted(top_level_dirs)
    framework_signals = _detect_framework_signals(file_paths)
    architecture_hints = _detect_architecture_hints(sorted_dirs, file_paths)

    return CodebaseMetadata(
        total_files=len(file_paths),
        extension_counts=dict(sorted(ext_counts.items(), key=lambda item: item[0])),
        detected_languages=detected_languages,
        top_level_directories=sorted_dirs,
        architecture_hints=architecture_hints,
        framework_signals=framework_signals,
        dependency_files=sorted(dependency_files),
    )
