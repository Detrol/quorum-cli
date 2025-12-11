"""Model provider utilities."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .config import get_settings


def format_display_name(model_id: str) -> str:
    """Generate a friendly display name from model ID.

    Examples:
        claude-opus-4-5-20251101 → Claude Opus 4.5
        gpt-5.1-2025-11-13 → GPT 5.1
        grok-4-1-fast-reasoning → Grok 4.1 Fast Reasoning
        o3-mini → o3 Mini
    """
    name = model_id

    # Remove date suffixes (YYYYMMDD or YYYY-MM-DD)
    name = re.sub(r'-\d{4}-\d{2}-\d{2}$', '', name)
    name = re.sub(r'-\d{8}$', '', name)

    # Handle version patterns like "4-5" → "4.5" (but not "o3")
    name = re.sub(r'(\d)-(\d)', r'\1.\2', name)

    # Split on dashes and process
    parts = name.split('-')

    # Uppercase mappings
    uppercase = {'gpt', 'xai', 'api'}

    result = []
    for part in parts:
        if not part:
            continue
        if part.lower() in uppercase:
            result.append(part.upper())
        elif part[0].isdigit() or part in ('o1', 'o3', 'o4'):
            # Keep version numbers and o-series as-is
            result.append(part)
        else:
            result.append(part.capitalize())

    return ' '.join(result)


@dataclass
class ModelInfo:
    """Information about an available model."""

    id: str
    provider: str
    display_name: str | None = None


def list_all_models_sync() -> dict[str, list[ModelInfo]]:
    """Return models configured in .env with auto-generated display names.

    Note: Ollama models are NOT included here - they are auto-discovered
    separately via discover_ollama_models().
    """
    settings = get_settings()

    result = {}
    for provider in ["openai", "anthropic", "google", "xai"]:
        models = settings.get_models_with_display_names(provider)
        result[provider] = [
            ModelInfo(id=model_id, provider=provider, display_name=display_name)
            for model_id, display_name in models
        ]
    return result


def get_provider_for_model(model_id: str) -> str | None:
    """Get provider by looking up model in .env configuration.

    Cloud providers (OpenAI, Anthropic, Google, xAI) require models to be
    listed in their respective *_MODELS environment variables.

    Ollama is a special case: models are auto-discovered and use prefix-based
    routing with the "ollama:" prefix.

    Args:
        model_id: The model identifier (e.g., "gpt-4.1", "claude-opus-4-5", "ollama:llama3")

    Returns:
        Provider name ("openai", "anthropic", "google", "xai", "ollama")
        or None if model not configured.
    """
    # Special case: Ollama prefix-based routing (auto-discovered models)
    if model_id.startswith("ollama:"):
        return "ollama"

    # Cloud providers: lookup in .env configuration
    settings = get_settings()
    for provider in ["openai", "anthropic", "google", "xai"]:
        configured_models = settings.get_models(provider)
        if model_id in configured_models:
            return provider

    return None  # Model not in configuration


async def discover_ollama_models(timeout: float = 5.0) -> list[tuple[str, str]]:
    """Discover available models from Ollama server.

    Queries the Ollama API to get a list of locally available models.
    Models are returned with the "ollama:" prefix for provider routing.

    Security measures:
    - Validates response structure before processing
    - Validates model names to prevent injection
    - Limits number of models returned

    Args:
        timeout: HTTP request timeout in seconds.

    Returns:
        List of (model_id, display_name) tuples, e.g., [("ollama:llama3", "Llama3")]
        Returns empty list if Ollama is not configured or unreachable.
    """
    import httpx

    # Model name validation pattern (alphanumeric, dash, underscore, colon, dot)
    model_name_pattern = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9\-_:.]*$')
    max_models = 100  # Limit models to prevent DoS

    settings = get_settings()
    if not settings.has_ollama:
        return []

    headers = {}
    if settings.ollama_api_key:
        headers["Authorization"] = f"Bearer {settings.ollama_api_key}"

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(
                f"{settings.ollama_base_url}/api/tags",
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()

            # Validate response structure
            if not isinstance(data, dict):
                return []

            models_data = data.get("models")
            if not isinstance(models_data, list):
                return []

            models = []
            for m in models_data[:max_models]:  # Limit number of models
                if not isinstance(m, dict):
                    continue

                name = m.get("name")
                if not isinstance(name, str) or not name:
                    continue

                # Validate model name format
                if len(name) > 100 or not model_name_pattern.match(name):
                    continue

                model_id = f"ollama:{name}"
                display_name = format_display_name(name)
                models.append((model_id, display_name))

            return models
    except (httpx.ConnectError, httpx.TimeoutException):
        # Ollama not running or unreachable - expected case
        return []
    except httpx.HTTPStatusError:
        # Server error from Ollama
        return []
    except Exception:
        # Unexpected error - still return empty list but this could be logged
        return []
