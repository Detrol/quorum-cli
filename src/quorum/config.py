"""Configuration and environment settings."""

from __future__ import annotations

import json
import os
import re
import stat
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# API key validation patterns and lengths
API_KEY_MIN_LENGTH = 20  # Minimum reasonable API key length
API_KEY_MAX_LENGTH = 200  # Maximum reasonable API key length

# Test mode flag - when True, skips home directory validation in _write_secure_file()
# Only set this in test fixtures, never in production code
_TEST_MODE = False


def _write_secure_file(path: Path, content: str) -> None:
    """Write content to file with restrictive permissions (0600).

    Creates parent directories if needed. File is only readable/writable by owner.

    Security: Re-validates path at write time to prevent TOCTOU (time-of-check-
    time-of-use) attacks where a symlink could be swapped in between validation
    and the actual write operation.

    Note: Home directory validation can be bypassed with _TEST_MODE for testing.
    Symlink checks are always performed regardless of test mode.
    """
    # Re-resolve and validate at write time (TOCTOU protection)
    resolved = path.resolve(strict=False)

    # Home directory validation (skipped in test mode)
    if not _TEST_MODE:
        home = Path.home().resolve()

        # Check path is still under home directory
        try:
            resolved.relative_to(home)
        except ValueError:
            raise ValueError(f"Path escaped home directory at write time: {path}")

        # Check parent chain for symlinks (requires home as stop point)
        current = resolved.parent
        while current != home and current != current.parent:
            if current.exists() and current.is_symlink():
                raise ValueError(f"Parent symlink detected at write time: {current}")
            current = current.parent

    # Check no symlinks appeared since validation (always check, even in test mode)
    if resolved.exists() and resolved.is_symlink():
        raise ValueError(f"Symlink detected at write time: {path}")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    # Set file permissions to owner read/write only (0600)
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)

# Cache files
CACHE_DIR = Path.home() / ".quorum"
VALIDATED_MODELS_CACHE = CACHE_DIR / "validated_models.json"
USER_SETTINGS_CACHE = CACHE_DIR / "settings.json"
INPUT_HISTORY_CACHE = CACHE_DIR / "history.json"


def get_validated_models_cache() -> set[str]:
    """Load validated models from cache."""
    if not VALIDATED_MODELS_CACHE.exists():
        return set()
    try:
        data = json.loads(VALIDATED_MODELS_CACHE.read_text())
        return set(data.get("models", []))
    except (json.JSONDecodeError, OSError, KeyError, TypeError):
        # Corrupted or inaccessible cache file - return empty set
        return set()


def save_validated_model(model_id: str) -> None:
    """Add a model to the validated cache."""
    cache = get_validated_models_cache()
    cache.add(model_id)
    _write_secure_file(VALIDATED_MODELS_CACHE, json.dumps({"models": list(cache)}))


def get_user_settings() -> dict:
    """Load user settings from cache."""
    if not USER_SETTINGS_CACHE.exists():
        return {}
    try:
        return json.loads(USER_SETTINGS_CACHE.read_text())
    except (json.JSONDecodeError, OSError):
        # Corrupted or inaccessible settings file - return empty dict
        return {}


# Allowed user settings keys with their expected types and validators
ALLOWED_USER_SETTINGS: dict[str, tuple[type, callable | None]] = {
    "selected_models": (list, lambda v: all(isinstance(m, str) for m in v)),
    "discussion_method": (str, lambda v: v in {"standard", "oxford", "advocate", "socratic", "delphi", "brainstorm", "tradeoff"}),
    "synthesizer_mode": (str, lambda v: v in {"first", "random", "rotate"}),
    "max_turns": (int, lambda v: 1 <= v <= 100),
}


def save_user_settings(settings: dict) -> None:
    """Save user settings to cache (merges with existing).

    Only whitelisted settings are saved. Unknown keys are silently ignored
    to prevent injection attacks.
    """
    if not isinstance(settings, dict):
        raise ValueError("settings must be a dictionary")

    current = get_user_settings()

    # Filter and validate settings
    for key, value in settings.items():
        if key not in ALLOWED_USER_SETTINGS:
            # Silently ignore unknown keys for security
            continue

        expected_type, validator = ALLOWED_USER_SETTINGS[key]

        # Type check
        if not isinstance(value, expected_type):
            raise ValueError(f"Invalid type for {key}: expected {expected_type.__name__}")

        # Additional validation if provided
        if validator and not validator(value):
            raise ValueError(f"Invalid value for {key}")

        current[key] = value

    _write_secure_file(USER_SETTINGS_CACHE, json.dumps(current, indent=2))


def get_input_history() -> list[str]:
    """Load input history from cache."""
    if not INPUT_HISTORY_CACHE.exists():
        return []
    try:
        data = json.loads(INPUT_HISTORY_CACHE.read_text())
        return data.get("history", [])
    except (json.JSONDecodeError, OSError, KeyError, TypeError):
        # Corrupted or inaccessible history file - return empty list
        return []


def add_to_input_history(input_text: str, max_items: int = 100) -> None:
    """Add an input to history (deduplicates and limits size)."""
    history = get_input_history()

    # Remove if already exists (will be re-added at end)
    if input_text in history:
        history.remove(input_text)

    history.append(input_text)

    # Limit size
    if len(history) > max_items:
        history = history[-max_items:]

    _write_secure_file(INPUT_HISTORY_CACHE, json.dumps({"history": history}))


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=(CACHE_DIR / ".env", ".env"),  # ~/.quorum/.env first, then ./.env
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API Keys
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    google_api_key: str | None = Field(default=None, alias="GOOGLE_API_KEY")
    xai_api_key: str | None = Field(default=None, alias="XAI_API_KEY")

    # Ollama (local models)
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    ollama_api_key: str | None = Field(default=None, alias="OLLAMA_API_KEY")

    # === OpenAI-compatible providers ===
    # These allow connecting to services that use the OpenAI API format:
    # OpenRouter, LM Studio, llama-swap, LocalAI, vLLM, etc.

    # OpenRouter (multi-model aggregator)
    openrouter_api_key: str | None = Field(default=None, alias="OPENROUTER_API_KEY")
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1", alias="OPENROUTER_BASE_URL"
    )
    openrouter_models: str = Field(default="", alias="OPENROUTER_MODELS")

    # LM Studio (local desktop app)
    lmstudio_api_key: str | None = Field(default=None, alias="LMSTUDIO_API_KEY")
    lmstudio_base_url: str = Field(
        default="http://localhost:1234/v1", alias="LMSTUDIO_BASE_URL"
    )
    lmstudio_models: str = Field(default="", alias="LMSTUDIO_MODELS")

    # llama-swap (hot-swap server for local models)
    llamaswap_api_key: str | None = Field(default=None, alias="LLAMASWAP_API_KEY")
    llamaswap_base_url: str | None = Field(default=None, alias="LLAMASWAP_BASE_URL")
    llamaswap_models: str = Field(default="", alias="LLAMASWAP_MODELS")

    # Custom OpenAI-compatible endpoint (generic fallback)
    custom_api_key: str | None = Field(default=None, alias="CUSTOM_API_KEY")
    custom_base_url: str | None = Field(default=None, alias="CUSTOM_BASE_URL")
    custom_models: str = Field(default="", alias="CUSTOM_MODELS")

    # Model lists (comma-separated)
    openai_models: str = Field(default="", alias="OPENAI_MODELS")
    anthropic_models: str = Field(default="", alias="ANTHROPIC_MODELS")
    google_models: str = Field(default="", alias="GOOGLE_MODELS")
    xai_models: str = Field(default="", alias="XAI_MODELS")
    # Note: Ollama models are auto-discovered, no OLLAMA_MODELS needed

    @property
    def _provider_models_map(self) -> dict[str, str]:
        """Return mapping of provider names to their model strings."""
        return {
            "openai": self.openai_models,
            "anthropic": self.anthropic_models,
            "google": self.google_models,
            "xai": self.xai_models,
            # OpenAI-compatible providers
            "openrouter": self.openrouter_models,
            "lmstudio": self.lmstudio_models,
            "llamaswap": self.llamaswap_models,
            "custom": self.custom_models,
        }

    # Defaults
    default_max_turns: int = Field(default=20, ge=1, le=100)

    # === Quorum configuration ===

    # Language: None = match question language, or force a specific language
    default_language: str | None = Field(default=None, alias="QUORUM_DEFAULT_LANGUAGE")

    # === Standard method configuration ===
    # These settings ONLY apply to Standard method. Other methods (Oxford, Advocate,
    # Socratic) have authentic structures with fixed flows.

    # Synthesizer mode for Standard: first, random, rotate
    # - first: Always use the first selected model (predictable)
    # - random: Randomly select a model each time
    # - rotate: Rotate through models across discussions
    synthesizer_mode: str = Field(default="first", alias="QUORUM_SYNTHESIZER")

    # Rounds per agent in Standard Phase 3 discussion (default: 2)
    # Total discussion messages = rounds_per_agent * number_of_models
    rounds_per_agent: int = Field(default=2, ge=1, le=10, alias="QUORUM_ROUNDS_PER_AGENT")

    # Auto-save directory: automatically saves all discussions (always markdown)
    # Defaults to ~/reports, supports ~ for home directory expansion
    report_dir: str = Field(default="~/reports", alias="QUORUM_REPORT_DIR")

    # Export settings for manual /export command
    export_dir: str | None = Field(default=None, alias="QUORUM_EXPORT_DIR")
    export_format: str = Field(default="md", alias="QUORUM_EXPORT_FORMAT")

    # Model response timeout in seconds (default: 60)
    # Increase for slow local models (e.g., Ollama on CPU)
    model_timeout: int = Field(default=60, ge=10, le=600, alias="QUORUM_MODEL_TIMEOUT")

    # Execution mode for parallel phases: "auto", "parallel", "sequential"
    # - auto (default): Run cloud APIs in parallel, local models (Ollama) sequentially
    # - parallel: Always run all models in parallel (best for cloud-only setups)
    # - sequential: Always run models one at a time (best for limited VRAM)
    execution_mode: str = Field(default="auto", alias="QUORUM_EXECUTION_MODE")

    @field_validator("execution_mode", mode="after")
    @classmethod
    def validate_execution_mode(cls, v: str) -> str:
        """Validate execution mode value."""
        valid_modes = {"auto", "parallel", "sequential"}
        if v not in valid_modes:
            raise ValueError(f"execution_mode must be one of {valid_modes}")
        return v

    @field_validator(
        "openai_api_key", "anthropic_api_key", "google_api_key", "xai_api_key",
        "ollama_api_key", "openrouter_api_key", "lmstudio_api_key",
        "llamaswap_api_key", "custom_api_key",
        mode="after"
    )
    @classmethod
    def validate_api_key(cls, v: str | None) -> str | None:
        """Validate API key format and length.

        Security measures:
        - Rejects keys that are too short (likely invalid)
        - Rejects keys that are too long (potential injection)
        - Only allows alphanumeric characters, dashes, and underscores
        """
        if v is None:
            return None

        # Length validation
        if len(v) < API_KEY_MIN_LENGTH:
            raise ValueError(f"API key too short (min {API_KEY_MIN_LENGTH} chars)")
        if len(v) > API_KEY_MAX_LENGTH:
            raise ValueError(f"API key too long (max {API_KEY_MAX_LENGTH} chars)")

        # Character validation - allow alphanumeric, dash, underscore, colon (for some providers)
        if not re.match(r'^[a-zA-Z0-9\-_:]+$', v):
            raise ValueError("API key contains invalid characters")

        return v

    @field_validator("synthesizer_mode", mode="after")
    @classmethod
    def validate_synthesizer_mode(cls, v: str) -> str:
        """Validate synthesizer mode value."""
        valid_modes = {"first", "random", "rotate"}
        if v not in valid_modes:
            raise ValueError(f"synthesizer_mode must be one of {valid_modes}")
        return v

    @field_validator("ollama_base_url", mode="after")
    @classmethod
    def validate_ollama_url(cls, v: str) -> str:
        """Validate that Ollama URL is localhost or private network.

        Security measure: Prevents SSRF attacks where attacker could point
        Ollama URL to internal services or external malicious endpoints.
        Only localhost and private IP ranges are allowed.
        """
        import ipaddress
        from urllib.parse import urlparse

        parsed = urlparse(v)
        host = parsed.hostname or ""

        # Allow localhost
        if host in ("localhost", "127.0.0.1", "::1"):
            return v

        # Check if it's a private IP
        try:
            ip = ipaddress.ip_address(host)
            if ip.is_private or ip.is_loopback:
                return v
            raise ValueError(
                f"Ollama URL must point to localhost or private network, got public IP: {host}"
            )
        except ValueError:
            # Not a valid IP - could be a hostname
            # Only allow explicit localhost variants
            if host.lower() in ("localhost", "host.docker.internal"):
                return v
            # Docker/container network hostnames
            if host.endswith(".local") or host.endswith(".internal"):
                return v
            raise ValueError(
                f"Ollama URL must point to localhost or private network. "
                f"Got: {host}. Allowed: localhost, 127.0.0.1, private IPs, .local/.internal domains"
            )

    def get_report_dir(self) -> Path:
        """Get expanded report directory path.

        Returns:
            Validated path for report storage.

        Raises:
            ValueError: If path is outside allowed boundaries.
        """
        return self._validate_safe_path(self.report_dir)

    def get_export_dir(self) -> Path | None:
        """Get expanded export directory path, or None if not configured.

        Returns:
            Validated path for exports, or None if not configured.

        Raises:
            ValueError: If path is outside allowed boundaries.
        """
        if not self.export_dir:
            return None
        return self._validate_safe_path(self.export_dir)

    def _validate_safe_path(self, path: str) -> Path:
        """Validate that a path is within allowed boundaries (defense in depth).

        Prevents path traversal attacks by ensuring paths resolve to
        safe locations (under home directory only). Uses is_relative_to()
        for robust path checking instead of string prefix matching.

        Security measures:
        - Only allows paths under home directory (no /tmp to prevent privilege escalation)
        - Uses Path.is_relative_to() to avoid string prefix bypass attacks
        - Rejects symlinks to prevent symlink-based traversal
        - Validates parent directory chain for symlinks

        Args:
            path: The path string to validate.

        Returns:
            Resolved, validated Path object.

        Raises:
            ValueError: If path is outside allowed boundaries or is a symlink.
        """
        # Step 1: Expand and resolve to canonical path
        try:
            expanded = Path(path).expanduser().resolve(strict=False)
        except (RuntimeError, OSError) as e:
            raise ValueError(f"Invalid path: {path} - {e}")

        home = Path.home().resolve()

        # Step 2: Check if expanded is child of home directory
        # Use is_relative_to() for robust checking (avoids /home/user-evil bypass)
        try:
            expanded.relative_to(home)
        except ValueError:
            raise ValueError(
                f"Path must be under home directory: {path} "
                f"(resolved to {expanded}, home={home})"
            )

        # Step 3: Reject symlinks to prevent privilege escalation
        # An attacker could create ~/reports -> /etc/cron.d to write cron jobs
        if expanded.exists() and expanded.is_symlink():
            raise ValueError(
                f"Symlinks not allowed for security reasons: {path} "
                f"(resolved to {expanded})"
            )

        # Step 4: Check parent directories aren't symlinks either
        # Prevents ~/safe/link -> /malicious/ attacks
        current = expanded
        while current != home and current != current.parent:
            if current.exists() and current.is_symlink():
                raise ValueError(
                    f"Path contains symlink component: {path} "
                    f"(symlink at {current})"
                )
            current = current.parent

        return expanded

    def get_models(self, provider: str) -> list[str]:
        """Get configured models for a provider (IDs only)."""
        models_str = self._provider_models_map.get(provider, "")
        if not models_str:
            return []
        result = []
        for entry in models_str.split(","):
            entry = entry.strip()
            if not entry:
                continue
            # Support "model-id|Display Name" format - extract just the ID
            model_id = entry.split("|", 1)[0].strip()
            result.append(model_id)
        return result

    def get_models_with_display_names(self, provider: str) -> list[tuple[str, str]]:
        """Get configured models with display names.

        Supports manual override: "model-id|Display Name"
        Otherwise auto-generates from model ID.

        Returns list of (model_id, display_name) tuples.
        """
        from .providers import format_display_name

        models_str = self._provider_models_map.get(provider, "")
        if not models_str:
            return []

        result = []
        for entry in models_str.split(","):
            entry = entry.strip()
            if not entry:
                continue
            if "|" in entry:
                model_id, display_name = entry.split("|", 1)
                result.append((model_id.strip(), display_name.strip()))
            else:
                result.append((entry, format_display_name(entry)))
        return result

    @property
    def has_openai(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def has_anthropic(self) -> bool:
        return bool(self.anthropic_api_key)

    @property
    def has_google(self) -> bool:
        return bool(self.google_api_key)

    @property
    def has_xai(self) -> bool:
        return bool(self.xai_api_key)

    @property
    def has_ollama(self) -> bool:
        return bool(self.ollama_base_url)

    # OpenAI-compatible providers
    @property
    def has_openrouter(self) -> bool:
        """OpenRouter is available if API key is set."""
        return bool(self.openrouter_api_key)

    @property
    def has_lmstudio(self) -> bool:
        """LM Studio is available if models are configured (no API key required)."""
        return bool(self.lmstudio_models)

    @property
    def has_llamaswap(self) -> bool:
        """llama-swap is available if base URL and models are configured."""
        return bool(self.llamaswap_base_url and self.llamaswap_models)

    @property
    def has_custom(self) -> bool:
        """Custom endpoint is available if base URL and models are configured."""
        return bool(self.custom_base_url and self.custom_models)

    @property
    def available_providers(self) -> list[str]:
        """List all available providers (native + OpenAI-compatible)."""
        providers = []
        # Native providers
        if self.has_openai:
            providers.append("openai")
        if self.has_anthropic:
            providers.append("anthropic")
        if self.has_google:
            providers.append("google")
        if self.has_xai:
            providers.append("xai")
        if self.has_ollama:
            providers.append("ollama")
        # OpenAI-compatible providers
        if self.has_openrouter:
            providers.append("openrouter")
        if self.has_lmstudio:
            providers.append("lmstudio")
        if self.has_llamaswap:
            providers.append("llamaswap")
        if self.has_custom:
            providers.append("custom")
        return providers


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
