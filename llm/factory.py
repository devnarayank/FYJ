import logging
from typing import Any

from config.settings import AppSettings

logger = logging.getLogger(__name__)

#: Providers are announced once per task instead of on every call.
_announced: set[str] = set()


def _announce_provider(provider: str, task: str) -> None:
    if task in _announced:
        return
    _announced.add(task)
    logger.info("Using %s model provider for %s", provider, task)


def _resolve_primary_model(settings: AppSettings) -> str:
    provider = (getattr(settings, "model_provider", "ollama") or "ollama").lower()
    return provider


def build_llm(settings: AppSettings, *, task: str = "chat"):
    """Build an LLM client following the configured provider preference.

    Primary provider is Ollama (local, free, private). Groq is used as fallback
    when Ollama is unavailable or disabled. The returned object exposes a standard
    `invoke(messages)` interface compatible with LangChain message objects.
    """
    provider = _resolve_primary_model(settings)

    if provider == "ollama":
        try:
            from langchain_ollama import ChatOllama

            _announce_provider("Ollama", task)
            return ChatOllama(
                model=getattr(settings.ollama, "model", "gpt-oss:120b-cloud "),
                base_url=getattr(settings.ollama, "base_url", "http://localhost:11434"),
                temperature=0.1,
            )
        except Exception as exc:
            logger.warning("Ollama unavailable, falling back to Groq: %s", exc)

    if settings.groq.api_key:
        try:
            from langchain_groq import ChatGroq

            _announce_provider("Groq fallback", task)
            return ChatGroq(
                model=settings.groq.model,
                api_key=settings.groq.api_key,
                temperature=0.1,
                max_tokens=4000,
            )
        except Exception as exc:
            logger.warning("Groq fallback unavailable: %s", exc)

    raise RuntimeError(
        "No LLM provider is configured. Set OLLAMA_MODEL or GROQ_API_KEY in your environment."
    )


def build_llm_with_fallback(settings: AppSettings, *, task: str = "chat") -> Any:
    """Compatibility wrapper for older call sites that expect a single LLM factory."""
    return build_llm(settings, task=task)
