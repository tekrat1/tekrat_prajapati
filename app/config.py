"""Runtime configuration, read from environment variables (see .env.example)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR") or BASE_DIR / "data")

SUPPORTED_LANGUAGES = {"en": "English", "de": "German", "es": "Spanish"}


@dataclass(frozen=True)
class Settings:
    provider: str
    groq_api_key: str
    groq_model: str
    gemini_api_key: str
    gemini_model: str
    ollama_host: str
    ollama_model: str
    max_attempts: int


def get_settings() -> Settings:
    """Read settings fresh each call so tests can change env vars."""
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    provider = os.getenv("LLM_PROVIDER", "").strip().lower()
    if not provider:
        provider = "groq" if groq_key else "gemini" if gemini_key else "mock"
    return Settings(
        provider=provider,
        groq_api_key=groq_key,
        groq_model=os.getenv("GROQ_MODEL") or "llama-3.3-70b-versatile",
        gemini_api_key=gemini_key,
        gemini_model=os.getenv("GEMINI_MODEL") or "gemini-2.5-flash",
        ollama_host=(os.getenv("OLLAMA_HOST") or "http://localhost:11434").rstrip("/"),
        ollama_model=os.getenv("OLLAMA_MODEL") or "llama3.1",
        max_attempts=int(os.getenv("MAX_ATTEMPTS") or 3),
    )
