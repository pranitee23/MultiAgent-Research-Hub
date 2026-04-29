"""
Nexus — Application settings.

Supports 4 LLM providers via one config switch (LLM_PROVIDER).
All have free tiers. Change provider by editing one line in .env.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Literal


class Settings(BaseSettings):
    """Validated configuration from .env file."""

    # ── LLM Provider Selection ──────────────────────────
    llm_provider: Literal["groq", "gemini", "ollama"] = Field(
        default="groq",
        description="Which LLM provider to use",
    )

    # ── Groq (primary — free, fast) ─────────────────────
    groq_api_key: str = Field(
        default="",
        description="Groq API key from console.groq.com",
    )
    groq_model: str = Field(
        default="llama-3.3-70b-versatile",
        description="Groq model for heavy tasks (synthesizer, critic)",
    )
    groq_model_light: str = Field(
        default="llama-3.1-8b-instant",
        description="Groq model for light tasks (planner)",
    )

    # ── Google Gemini (backup — free) ───────────────────
    google_api_key: str = Field(
        default="",
        description="Gemini API key from aistudio.google.com",
    )
    gemini_model: str = Field(
        default="gemini-2.5-flash",
        description="Gemini model for heavy tasks",
    )
    gemini_model_light: str = Field(
        default="gemini-2.0-flash-lite",
        description="Gemini model for light tasks",
    )

    # ── Ollama (offline/local) ──────────────────────────
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama server URL",
    )
    ollama_model: str = Field(
        default="llama3.1:8b",
        description="Ollama model for heavy tasks",
    )
    ollama_model_light: str = Field(
        default="llama3.1:8b",
        description="Ollama model for light tasks (same if only one available)",
    )

    # ── Embeddings ──────────────────────────────────────
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2",
        description="Sentence-transformers model (runs locally)",
    )

    # ── Search ──────────────────────────────────────────
    arxiv_max_results: int = Field(default=5, ge=1, le=20)
    scholar_max_results: int = Field(default=5, ge=1, le=20)
    search_timeout_seconds: int = Field(default=30, ge=5, le=120)

    # ── Agent ───────────────────────────────────────────
    max_critic_revisions: int = Field(default=2, ge=0, le=5)

    # ── Logging ─────────────────────────────────────────
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="pretty")

    # ── LangSmith Tracing (optional) ─────────────────────
    langchain_tracing_v2: bool = Field(
        default=False,
        description="Enable LangSmith tracing for observability",
    )
    langchain_api_key: str = Field(
        default="",
        description="LangSmith API key",
    )
    langchain_project: str = Field(
        default="nexus-research-agent",
        description="LangSmith project name",
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# Singleton
settings = Settings()