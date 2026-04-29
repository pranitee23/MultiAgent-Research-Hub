"""
Nexus — LLM provider factory.

Call get_llm() anywhere in the project. It returns the configured
LLM based on LLM_PROVIDER in .env. Switch providers by changing
one line — zero code changes in agents.

Instances are cached by (provider, temperature) so repeated calls
reuse the same HTTP session and connection pool.

Usage in any agent file:
    from src.core.llm import get_llm
    llm = get_llm()                    # Uses default temp
    llm = get_llm(temperature=0.1)     # Custom temperature

Switch provider in .env:
    LLM_PROVIDER=groq      → Llama 3.3 70B on Groq (fast, free)
    LLM_PROVIDER=gemini    → Gemini 2.5 Flash (free)
    LLM_PROVIDER=ollama    → Local Llama 3.1 8B (offline)
"""

from functools import lru_cache
from src.config.settings import settings


@lru_cache(maxsize=16)
def get_llm(temperature: float = 0.3, tier: str = "heavy"):
    """Return a cached LLM instance.

    This is the ONLY place in the entire project that
    imports provider-specific LLM classes. Every agent
    calls this function instead of importing directly.

    Args:
        temperature: Sampling temperature.
        tier: "light" for cheap/fast tasks (planner),
              "heavy" for quality-critical tasks (synthesizer, critic).

    Instances are cached by (temperature, tier) so the same
    combo reuses the connection pool.
    """
    provider = settings.llm_provider

    if provider == "groq":
        from langchain_groq import ChatGroq
        if not settings.groq_api_key:
            raise ValueError(
                "GROQ_API_KEY not set in .env. "
                "Get a free key at https://console.groq.com"
            )
        model = settings.groq_model_light if tier == "light" else settings.groq_model
        return ChatGroq(
            model=model,
            api_key=settings.groq_api_key,
            temperature=temperature,
        )

    elif provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        if not settings.google_api_key:
            raise ValueError(
                "GOOGLE_API_KEY not set in .env. "
                "Get a free key at https://aistudio.google.com"
            )
        model = settings.gemini_model_light if tier == "light" else settings.gemini_model
        return ChatGoogleGenerativeAI(
            model=model,
            google_api_key=settings.google_api_key,
            temperature=temperature,
        )

    elif provider == "ollama":
        from langchain_ollama import ChatOllama
        model = settings.ollama_model_light if tier == "light" else settings.ollama_model
        return ChatOllama(
            model=model,
            base_url=settings.ollama_base_url,
            temperature=temperature,
        )

    else:
        raise ValueError(
            f"Unknown LLM_PROVIDER: '{provider}'. "
            f"Valid options: groq, gemini, ollama"
        )


def get_provider_info() -> dict:
    """Return info about the current provider (for health checks)."""
    provider = settings.llm_provider
    info = {"provider": provider}

    if provider == "groq":
        info["model"] = settings.groq_model
        info["has_key"] = bool(settings.groq_api_key)
        info["speed"] = "~500 tokens/sec"
        info["cost"] = "$0 (free tier)"
    elif provider == "gemini":
        info["model"] = settings.gemini_model
        info["has_key"] = bool(settings.google_api_key)
        info["speed"] = "~100 tokens/sec"
        info["cost"] = "$0 (free tier)"
    elif provider == "ollama":
        info["model"] = settings.ollama_model
        info["has_key"] = True  # No key needed
        info["speed"] = "~10 tokens/sec (CPU)"
        info["cost"] = "$0 (local)"

    return info