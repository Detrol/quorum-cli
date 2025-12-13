"""Application-wide constants for Quorum.

Centralizes magic numbers, limits, and configuration values.
"""

# =============================================================================
# Version Information
# =============================================================================

__version__ = "1.0.7"
"""Quorum application version."""

PROTOCOL_VERSION = "1.0.0"
"""JSON-RPC protocol version between backend and frontend.

Format: MAJOR.MINOR.PATCH
- MAJOR: Breaking changes (incompatible)
- MINOR: New features (backward compatible)
- PATCH: Bug fixes
"""


# =============================================================================
# Model & Discussion Limits
# =============================================================================

MAX_MODELS = 20
"""Maximum number of models allowed in a discussion."""

MAX_MODEL_ID_LENGTH = 100
"""Maximum length of a model ID string."""

MAX_QUESTION_LENGTH = 50_000
"""Maximum question length in characters (50KB)."""

MAX_POOL_SIZE = 20
"""Maximum number of model clients to keep in connection pool."""


# =============================================================================
# Error Message Formatting
# =============================================================================

ERROR_MESSAGE_MAX_LENGTH = 500
"""Maximum length for error messages in responses."""

CRITIQUE_ERROR_MAX_LENGTH = 300
"""Maximum length for error messages in critique phase."""


# =============================================================================
# Timeouts (seconds)
# =============================================================================

MODEL_TIMEOUT_SECONDS = 60
"""Default timeout for model API calls (1 minute)."""

PAUSE_TIMEOUT_SECONDS = 300
"""Timeout for pause/resume operations (5 minutes)."""


# =============================================================================
# Rate Limiting
# =============================================================================

RATE_LIMIT_REQUESTS_PER_MINUTE = 60
"""Maximum requests per minute for rate limiting."""

RATE_LIMIT_BURST_SIZE = 10
"""Maximum burst size for rate limiter."""


# =============================================================================
# Connection Pool
# =============================================================================

HTTP_POOL_MAX_CONNECTIONS = 100
"""Maximum total HTTP connections in pool."""

HTTP_POOL_MAX_KEEPALIVE = 20
"""Maximum keepalive connections per host."""

HTTP_CONNECT_TIMEOUT = 10.0
"""Timeout for establishing HTTP connection (seconds)."""

HTTP_READ_TIMEOUT = 60.0
"""Timeout for reading HTTP response (1 minute)."""


# =============================================================================
# Discussion Memory Limits
# =============================================================================

MAX_DISCUSSION_HISTORY_MESSAGES = 50
"""Maximum messages to keep in discussion history (sliding window)."""

MAX_MESSAGE_SIZE = 50_000
"""Maximum size of a single message in characters (50KB).

Messages exceeding this limit will be truncated to prevent memory exhaustion
from verbose AI responses.
"""

MAX_HISTORY_TOTAL_SIZE = 2_000_000
"""Maximum total size of discussion history in characters (2MB).

When exceeded, oldest messages are evicted to make room. This prevents
memory exhaustion during long discussions with multiple agents.
"""

MAX_IPC_EVENT_QUEUE_SIZE = 100
"""Maximum events in IPC backpressure queue."""

MAX_JSON_REQUEST_SIZE = 1_000_000
"""Maximum JSON request size in bytes (1MB).

Requests exceeding this limit are rejected before parsing to prevent
memory exhaustion DoS attacks.
"""

PHASE_TIMEOUT_SECONDS = 300
"""Timeout for entire parallel phase execution (5 minutes)."""


# =============================================================================
# Fast Provider Detection (no pydantic dependency)
# =============================================================================

def get_available_providers_fast() -> list[str]:
    """Get list of available providers by checking environment variables.

    This is a lightweight alternative to Settings.available_providers that
    doesn't require loading pydantic. Used during startup to avoid ~1.6s
    import delay.

    Returns:
        List of provider names with configured API keys.
    """
    import os

    providers = []
    if os.environ.get("OPENAI_API_KEY"):
        providers.append("openai")
    if os.environ.get("ANTHROPIC_API_KEY"):
        providers.append("anthropic")
    if os.environ.get("GOOGLE_API_KEY"):
        providers.append("google")
    if os.environ.get("XAI_API_KEY"):
        providers.append("xai")
    # Ollama is available if base URL is set (defaults to localhost)
    if os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"):
        providers.append("ollama")
    return providers
