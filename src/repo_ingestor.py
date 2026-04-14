"""Repository ingestion for the Observe stage."""

from __future__ import annotations

from pathlib import Path
import tempfile
from urllib.parse import urlparse

from git import GitCommandError, Repo

from src.config import Settings
from src.models import RepoIngestionResult


SKIP_DIRS = {
    ".git",
    ".idea",
    ".vscode",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".venv",
    "venv",
    ".mypy_cache",
    ".pytest_cache",
}

KEY_FILE_CANDIDATES = [
    "README.md",
    "requirements.txt",
    "pyproject.toml",
    "package.json",
    "Dockerfile",
    "docker-compose.yml",
    ".github/workflows",
]


def _is_url(value: str) -> bool:
    parsed = urlparse(value)
    if parsed.scheme in {"http", "https", "ssh", "git"}:
        return True
    return value.startswith("git@")


def _safe_repo_name(repo_input: str) -> str:
    if _is_url(repo_input):
        name = Path(urlparse(repo_input).path).stem
        return name or "repo"
    return Path(repo_input).resolve().name


def _build_unique_clone_path(clone_root: Path, repo_name: str) -> Path:
    """
    Create a non-conflicting clone path for repeated runs.

    Why this exists:
    - Avoids clone failures when a previous temp folder already exists.
    - Keeps reruns reliable on Windows where folder deletion can fail due to locks.
    """
    base_path = clone_root / repo_name
    if not base_path.exists():
        return base_path

    suffix = 1
    while True:
        candidate = clone_root / f"{repo_name}_{suffix}"
        if not candidate.exists():
            return candidate
        suffix += 1


def _collect_files(root_path: Path, max_files: int) -> list[str]:
    file_paths: list[str] = []
    for path in root_path.rglob("*"):
        if path.is_dir() and path.name in SKIP_DIRS:
            continue
        if not path.is_file():
            continue
        if any(skip in path.parts for skip in SKIP_DIRS):
            continue
        rel_path = path.relative_to(root_path).as_posix()
        file_paths.append(rel_path)
        if len(file_paths) >= max_files:
            break
    return sorted(file_paths)


def _collect_key_files(root_path: Path) -> dict[str, str]:
    key_files: dict[str, str] = {}
    for candidate in KEY_FILE_CANDIDATES:
        candidate_path = root_path / candidate
        if candidate_path.exists():
            key_files[candidate] = candidate_path.as_posix()
    return key_files


def _read_readme_excerpt(root_path: Path, max_chars: int) -> str:
    readme_path = root_path / "README.md"
    if not readme_path.exists():
        return ""
    try:
        return readme_path.read_text(encoding="utf-8", errors="ignore")[:max_chars]
    except OSError:
        return ""


def ingest_repository(repo_input: str, settings: Settings) -> RepoIngestionResult:
    """
    Clone or open a repository and gather a lightweight repository snapshot.

    Why this exists:
    - Gives the agent deterministic context before any reasoning.
    - Keeps analysis read-only and bounded for MVP scope.
    """
    repo_name = _safe_repo_name(repo_input)
    clone_root = Path(settings.clone_root)
    clone_root.mkdir(parents=True, exist_ok=True)

    source_type = "local"
    if _is_url(repo_input):
        source_type = "cloned"
        repo_path = _build_unique_clone_path(clone_root, repo_name)
        try:
            Repo.clone_from(repo_input, repo_path)
        except GitCommandError as exc:
            # Some Windows setups block git writes in project folders.
            # Retry in OS temp so learning flow is not interrupted.
            if "Permission denied" not in str(exc):
                raise
            fallback_root = Path(tempfile.gettempdir()) / "archlens_tmp"
            fallback_root.mkdir(parents=True, exist_ok=True)
            repo_path = _build_unique_clone_path(fallback_root, repo_name)
            Repo.clone_from(repo_input, repo_path)
    else:
        repo_path = Path(repo_input).resolve()
        if not repo_path.exists():
            raise FileNotFoundError(f"Repository path does not exist: {repo_path}")

    file_paths = _collect_files(repo_path, settings.max_files_to_scan)
    key_files = _collect_key_files(repo_path)
    readme_excerpt = _read_readme_excerpt(repo_path, settings.max_readme_chars)

    return RepoIngestionResult(
        repo_name=repo_name,
        repo_path=repo_path.as_posix(),
        source_type=source_type,
        file_paths=file_paths,
        key_files=key_files,
        readme_excerpt=readme_excerpt,
    )
