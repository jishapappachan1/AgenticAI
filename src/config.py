"""Configuration helpers for ArchLens."""

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables."""

    gemini_api_key: str
    gemini_model: str = "gemini-2.0-flash"
    max_files_to_scan: int = 2000
    max_readme_chars: int = 3000
    clone_root: str = ".archlens_tmp"


def get_settings() -> Settings:
    """Load environment variables and return validated settings."""
    # Resolve .env from project root and override stale process env values.
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(dotenv_path=env_path, override=True)

    return Settings(
        gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip(),
        max_files_to_scan=int(os.getenv("MAX_FILES_TO_SCAN", "2000")),
        max_readme_chars=int(os.getenv("MAX_README_CHARS", "3000")),
        clone_root=os.getenv("CLONE_ROOT", ".archlens_tmp").strip(),
    )
