"""Markdown report generation for architecture reviews."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re

from src.models import ArchitectureReview


def _bulletize(items: list[str]) -> str:
    if not items:
        return "- Not enough evidence to list items."
    return "\n".join(f"- {item}" for item in items)


def render_markdown_report(review: ArchitectureReview, repo_input: str) -> str:
    """
    Convert structured review output into a readable markdown report.

    Why this exists:
    - Keeps presentation concerns separate from reasoning/orchestration logic.
    """
    generated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    return (
        "# AI Architecture Review Report\n\n"
        f"**Repository Input:** `{repo_input}`\n\n"
        f"**Generated At:** {generated_at}\n\n"
        "## Architecture Overview\n"
        f"{review.architecture_overview or 'No overview generated.'}\n\n"
        "## Strengths\n"
        f"{_bulletize(review.strengths)}\n\n"
        "## Risks / Smells\n"
        f"{_bulletize(review.risks_smells)}\n\n"
        "## Recommendations\n"
        f"{_bulletize(review.recommendations)}\n\n"
        "## Confidence Note\n"
        f"{review.confidence_note or 'Moderate confidence based on repository-level evidence.'}\n"
    )


def save_markdown_report(markdown: str, output_dir: str, repo_name: str) -> str:
    """Persist markdown report and return saved path."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^a-zA-Z0-9_-]+", "-", repo_name).strip("-") or "repo"
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = Path(output_dir) / f"{safe_name}_architecture_review_{timestamp}.md"
    path.write_text(markdown, encoding="utf-8")
    return path.as_posix()
