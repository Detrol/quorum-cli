"""Model client factory for AI providers.

Provides unified client creation and connection pooling for multiple
AI providers: OpenAI, Anthropic, Google, xAI, and Ollama.
"""

from __future__ import annotations

import asyncio
import atexit
import logging
import re
from collections import OrderedDict

from .clients import AnthropicClient, ChatClient, OpenAIClient, UserMessage
from .config import get_settings
from .constants import (
    HTTP_CONNECT_TIMEOUT,
    HTTP_POOL_MAX_CONNECTIONS,
    HTTP_POOL_MAX_KEEPALIVE,
    HTTP_READ_TIMEOUT,
    MAX_POOL_SIZE,
)
from .providers import get_provider_for_model

logger = logging.getLogger(__name__)

# Module-level lock for thread-safe pool operations
# Created at module load time to avoid race condition in get_lock()
_pool_lock = asyncio.Lock()

# Shared HTTP client with connection pool limits
# Lazy-initialized to avoid import-time side effects
_shared_http_client = None


def _get_http_client():
    """Get or create shared HTTP client with connection pool limits.

    Uses httpx.AsyncClient with explicit limits for:
    - max_connections: Total connections in pool
    - max_keepalive_connections: Persistent connections per host
    - connect timeout and read timeout for reliability
    """
    global _shared_http_client
    if _shared_http_client is None:
        import httpx

        limits = httpx.Limits(
            max_connections=HTTP_POOL_MAX_CONNECTIONS,
            max_keepalive_connections=HTTP_POOL_MAX_KEEPALIVE,
        )
        timeout = httpx.Timeout(
            connect=HTTP_CONNECT_TIMEOUT,
            read=HTTP_READ_TIMEOUT,
            write=30.0,
            pool=5.0,
        )
        _shared_http_client = httpx.AsyncClient(limits=limits, timeout=timeout)
    return _shared_http_client


async def _close_http_client() -> None:
    """Close the shared HTTP client."""
    global _shared_http_client
    if _shared_http_client is not None:
        try:
            await _shared_http_client.aclose()
        except Exception as e:
            logger.debug("Error closing shared HTTP client: %s", e)
        _shared_http_client = None


class ClientPool:
    """Pool of reusable model clients to avoid connection overhead.

    This pool caches model clients by model_id, reusing existing connections
    instead of creating new HTTP clients for each API call. This reduces
    connection establishment overhead by 50-200ms per request.

    Thread-safe and supports async operations. Uses module-level lock to avoid
    race condition during lock creation.
    """

    _instance: "ClientPool | None" = None

    def __init__(self):
        # OrderedDict provides O(1) LRU operations via move_to_end() and popitem()
        self._clients: OrderedDict[str, ChatClient] = OrderedDict()
        # Register atexit handler for cleanup on shutdown
        atexit.register(self._cleanup_sync)

    def _cleanup_sync(self) -> None:
        """Synchronous cleanup for atexit (best effort).

        Called during interpreter shutdown. Uses purely synchronous cleanup
        to avoid race conditions with event loop shutdown.

        Note: During Python interpreter shutdown, the event loop may be in
        an inconsistent state. Attempting async operations can cause hangs
        or errors. We only do best-effort sync cleanup here.
        """
        import inspect

        # Best-effort synchronous cleanup only
        # Don't try to use async operations during interpreter shutdown
        for model_id, client in list(self._clients.items()):
            try:
                # Try to close the underlying httpx client synchronously
                # Most OpenAI-compatible clients wrap an httpx.AsyncClient
                if hasattr(client, "_client"):
                    underlying = client._client
                    if hasattr(underlying, "close"):
                        close_method = underlying.close
                        # Only call sync close methods - async ones can't be awaited here
                        if not inspect.iscoroutinefunction(close_method):
                            close_method()
                        # Skip async close - coroutine would be unawaited
                    elif hasattr(underlying, "_client") and hasattr(underlying._client, "close"):
                        # Some clients nest the httpx client deeper
                        nested_close = underlying._client.close
                        if not inspect.iscoroutinefunction(nested_close):
                            nested_close()
            except Exception as e:
                # Suppress errors during shutdown - this is best-effort only
                logger.debug("Error during sync cleanup for %s: %s", model_id, e)

        self._clients.clear()

    @classmethod
    def get_instance(cls) -> "ClientPool":
        """Get the singleton pool instance."""
        if cls._instance is None:
            cls._instance = ClientPool()
        return cls._instance

    async def get_client(self, model_id: str) -> ChatClient:
        """Get or create a client for the given model.

        Args:
            model_id: The model identifier (e.g., "gpt-4o")

        Returns:
            A reusable model client
        """
        async with _pool_lock:
            if model_id in self._clients:
                # O(1) move to end (most recently used)
                self._clients.move_to_end(model_id)
                return self._clients[model_id]

            # Evict oldest if pool is full - O(1) with popitem(last=False)
            while len(self._clients) >= MAX_POOL_SIZE:
                oldest, old_client = self._clients.popitem(last=False)
                # Don't close - shared HTTP client would break other clients
                # Just clear API key reference for security
                try:
                    old_client._api_key = None  # type: ignore[attr-defined]
                except AttributeError:
                    pass  # Client may not have _api_key
                logger.debug("Evicted client for %s from pool", oldest)

            # Create new client
            client = _create_model_client_internal(model_id)
            self._clients[model_id] = client
            return client

    async def close_all(self) -> None:
        """Clear all pooled clients (does not close shared HTTP client).

        Note: We don't close individual clients because OpenAI-compatible clients
        share a common HTTP client. Closing one would break all others.
        The shared HTTP client is closed separately by close_pool().
        """
        async with _pool_lock:
            for client in self._clients.values():
                # Clear API key reference for security
                try:
                    client._api_key = None  # type: ignore[attr-defined]
                except AttributeError:
                    pass  # Client may not have _api_key
            self._clients.clear()

    async def remove_client(self, model_id: str) -> None:
        """Remove a specific client from the pool (e.g., after error).

        Note: We do NOT close the client here because OpenAI-compatible clients
        share a common HTTP client. Closing one would break all others.
        The removed client will be garbage collected.

        Security: Clears API key reference to prevent memory persistence.
        """
        async with _pool_lock:
            if model_id in self._clients:
                client = self._clients.pop(model_id)
                # Clear API key reference to prevent memory persistence
                try:
                    client._api_key = None  # type: ignore[attr-defined]
                except AttributeError:
                    pass  # Client may not have _api_key


# Module-level pool instance
_pool = ClientPool.get_instance()


def _create_model_client_internal(model_id: str) -> ChatClient:
    """Create the appropriate model client based on model ID (internal use).

    Args:
        model_id: The model identifier (e.g., "gpt-4o", "claude-sonnet-4", "gemini-2.0-flash")

    Returns:
        A configured model client for the specified model.

    Raises:
        ValueError: If the provider cannot be detected or API key is missing.
    """
    settings = get_settings()
    provider = get_provider_for_model(model_id)

    if provider is None:
        # Generate helpful error message listing configured providers
        available_providers = [
            p for p in ["openai", "anthropic", "google", "xai"]
            if settings.get_models(p)
        ]
        providers_str = ", ".join(available_providers) if available_providers else "none"

        raise ValueError(
            f"Model '{model_id}' not found in configuration. "
            f"Available providers: {providers_str}. "
            f"Add model to appropriate *_MODELS list in .env, or use 'ollama:model-name' for local models."
        )

    if provider == "openai":
        if not settings.has_openai:
            raise ValueError("OpenAI API key not configured. Set OPENAI_API_KEY in .env")
        return OpenAIClient(
            model=model_id,
            api_key=settings.openai_api_key,
            http_client=_get_http_client(),
        )

    elif provider == "anthropic":
        if not settings.has_anthropic:
            raise ValueError(
                "Anthropic API key not configured. Set ANTHROPIC_API_KEY in .env"
            )
        return AnthropicClient(
            model=model_id,
            api_key=settings.anthropic_api_key,
        )

    elif provider == "google":
        if not settings.has_google:
            raise ValueError("Google API key not configured. Set GOOGLE_API_KEY in .env")
        # Gemini uses OpenAI-compatible API
        return OpenAIClient(
            model=model_id,
            api_key=settings.google_api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            http_client=_get_http_client(),
        )

    elif provider == "xai":
        if not settings.has_xai:
            raise ValueError("xAI API key not configured. Set XAI_API_KEY in .env")
        # Grok uses OpenAI-compatible API
        return OpenAIClient(
            model=model_id,
            api_key=settings.xai_api_key,
            base_url="https://api.x.ai/v1",
            http_client=_get_http_client(),
        )

    elif provider == "ollama":
        # Strip "ollama:" prefix to get actual model name for Ollama API
        actual_model = model_id.split(":", 1)[1] if ":" in model_id else model_id
        # Ollama uses OpenAI-compatible API at /v1
        return OpenAIClient(
            model=actual_model,
            api_key=settings.ollama_api_key or "ollama",  # Ollama ignores API key locally
            base_url=f"{settings.ollama_base_url}/v1",
            http_client=_get_http_client(),
        )

    raise ValueError(f"Unsupported provider: {provider}")


async def get_pooled_client(model_id: str) -> ChatClient:
    """Get a reusable client from the pool.

    This reuses HTTP connections for efficiency.

    Args:
        model_id: The model identifier

    Returns:
        A reusable model client from the pool
    """
    return await _pool.get_client(model_id)


async def close_pool() -> None:
    """Close all clients in the pool and shared HTTP client.

    Call this when shutting down the application.
    """
    await _pool.close_all()
    await _close_http_client()


async def clear_pool() -> None:
    """Clear all clients from the pool without closing the shared HTTP client.

    Call this on cancellation to prevent stale/corrupted connections
    from affecting subsequent discussions. The HTTP client is preserved
    for reuse.
    """
    await _pool.close_all()


async def remove_from_pool(model_id: str) -> None:
    """Remove a client from the pool (e.g., after error).

    Args:
        model_id: The model to remove
    """
    await _pool.remove_client(model_id)


def _extract_validation_error(error_str: str) -> str:
    """Extract clean error message for validation failures."""
    if "credit balance is too low" in error_str:
        return "Insufficient credits"
    if "model" in error_str.lower() and "not found" in error_str.lower():
        return "Model not found"
    if "invalid_api_key" in error_str.lower() or "invalid api key" in error_str.lower():
        return "Invalid API key"
    if "authentication" in error_str.lower():
        return "Authentication failed"
    if "rate_limit" in error_str.lower():
        return "Rate limited"
    if "quota" in error_str.lower():
        return "Quota exceeded"
    # Truncate long errors
    if len(error_str) > 60:
        return error_str[:60] + "..."
    return error_str


def _sanitize_error_string(error_str: str) -> str:
    """Remove sensitive data from error strings.

    Redacts API keys and bearer tokens that may appear in error messages
    to prevent accidental credential exposure in logs.
    """
    # Comprehensive redaction patterns for all provider key formats
    patterns = [
        # OpenAI keys (sk-...)
        r'sk-[a-zA-Z0-9\-_]{20,}',
        # Anthropic keys (sk-ant-...)
        r'sk-ant-[a-zA-Z0-9\-_]{20,}',
        # Google API keys (AIza...)
        r'AIza[a-zA-Z0-9\-_]{30,}',
        # xAI keys (xai-...)
        r'xai-[a-zA-Z0-9\-_]{20,}',
        # Generic Bearer tokens
        r'Bearer\s+[a-zA-Z0-9\-_:\.]{20,}',
        # Generic API key assignments (various formats)
        r'api[_-]?key["\']?\s*[:=]\s*["\']?[a-zA-Z0-9\-_:\.]{20,}',
        # URL query parameters with keys
        r'[?&]api[_-]?key=[a-zA-Z0-9\-_%]{20,}',
        # JSON format keys
        r'"(?:api[Kk]ey|token|authorization)"\s*:\s*"[a-zA-Z0-9\-_:\.]{20,}"',
    ]

    sanitized = error_str
    for pattern in patterns:
        sanitized = re.sub(pattern, '[REDACTED]', sanitized, flags=re.IGNORECASE)

    return sanitized


def extract_api_error(e: Exception, max_length: int = 500) -> str:
    """Extract clean error message from API exception.

    Tries to extract the user-friendly message from OpenAI SDK exceptions
    (which have e.body['message']), falling back to str(e) otherwise.

    Also logs the full error for debugging (sanitized).

    Args:
        e: The exception to extract message from.
        max_length: Maximum length for returned message.

    Returns:
        A clean, user-friendly error message.
    """
    # Log sanitized error for debugging (never log raw API keys)
    sanitized_full = _sanitize_error_string(str(e))
    logger.debug("API error (sanitized): %s", sanitized_full[:1000])

    # Try to extract message from OpenAI SDK exception format
    # These have e.body = {'message': '...', 'type': '...', 'code': '...'}
    if hasattr(e, "body") and isinstance(e.body, dict):
        message = e.body.get("message")
        if message:
            if len(message) > max_length:
                return message[:max_length] + "..."
            return message

    # Fallback: use str(e) but try to clean it up
    error_str = str(e)

    # If it looks like OpenAI SDK format, try to parse the message out
    # Format: "Error code: 429 - {'error': {'message': '...', 'type': '...'}}"
    if "'message':" in error_str:
        match = re.search(r"'message':\s*'([^']*)'", error_str)
        if match:
            message = match.group(1)
            if len(message) > max_length:
                return message[:max_length] + "..."
            return message

    # Final fallback: return truncated str(e)
    if len(error_str) > max_length:
        return error_str[:max_length] + "..."
    return error_str


async def validate_model(model_id: str, timeout: float | None = None) -> tuple[bool, str | None]:
    """Validate a model by making a minimal API call.

    Args:
        model_id: The model identifier to validate.
        timeout: Maximum time to wait for validation (seconds).
                 If None, uses 60s for Ollama models, 30s for others.

    Returns:
        Tuple of (success, error_message). If success is True, error_message is None.
    """
    import asyncio

    # Ollama models need longer timeout (must load into GPU/memory)
    if timeout is None:
        timeout = 60.0 if model_id.startswith("ollama:") else 30.0

    try:
        # Use pooled client - if validation succeeds, client stays in pool for reuse
        client = await get_pooled_client(model_id)

        # Minimal test - just check the model responds
        await asyncio.wait_for(
            client.create(messages=[UserMessage(content="Hi", source="validation")]),
            timeout=timeout
        )
        return (True, None)

    except asyncio.TimeoutError:
        # Remove failed client from pool
        await remove_from_pool(model_id)
        return (False, f"Timeout ({timeout}s)")

    except Exception as e:
        # Remove failed client from pool
        await remove_from_pool(model_id)
        error_msg = _extract_validation_error(str(e))
        return (False, error_msg)
