"""JSON-RPC IPC handler for Quorum.

Communicates with frontend via stdin/stdout using NDJSON (newline-delimited JSON).

NOTE: Heavy imports (team, models) are done lazily inside handlers
to minimize startup time. Only stdlib + light deps imported at top level.
"""

from __future__ import annotations

import asyncio
import json
import re
import sys
import uuid
from dataclasses import asdict, is_dataclass
from typing import Any

from .constants import (
    MAX_IPC_EVENT_QUEUE_SIZE,
    MAX_JSON_REQUEST_SIZE,
    MAX_MODEL_ID_LENGTH,
    MAX_MODELS,
    MAX_QUESTION_LENGTH,
    PAUSE_TIMEOUT_SECONDS,
    PROTOCOL_VERSION,
    RATE_LIMIT_BURST_SIZE,
    RATE_LIMIT_REQUESTS_PER_MINUTE,
    __version__,
    get_available_providers_fast,
)

# Lazy imports - these are heavy and slow down startup
# from .team import FourPhaseConsensusTeam, etc.

# === Input Validation Constants ===
MAX_MODEL_COUNT = MAX_MODELS  # Backward compatibility alias
# ReDoS-safe character whitelist (O(n) complexity, no backtracking)
MODEL_ID_VALID_CHARS = frozenset(
    'abcdefghijklmnopqrstuvwxyz'
    'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    '0123456789'
    '-_./:@'
)
VALID_METHODS = {"standard", "oxford", "advocate", "socratic", "delphi", "brainstorm", "tradeoff"}
VALID_SYNTHESIZER_MODES = {"first", "random", "rotate"}


# === Rate Limiter ===

class RateLimiter:
    """Token bucket rate limiter for request throttling.

    Allows burst of requests up to burst_size, then refills
    at requests_per_minute rate.
    """

    def __init__(
        self,
        requests_per_minute: int = RATE_LIMIT_REQUESTS_PER_MINUTE,
        burst_size: int = RATE_LIMIT_BURST_SIZE,
    ):
        """Initialize rate limiter.

        Args:
            requests_per_minute: Maximum sustained request rate.
            burst_size: Maximum burst size (initial tokens).
        """
        self._rate = requests_per_minute / 60.0  # tokens per second
        self._burst_size = burst_size
        self._tokens = float(burst_size)
        self._last_refill = asyncio.get_event_loop().time() if asyncio.get_event_loop().is_running() else 0.0

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        try:
            now = asyncio.get_event_loop().time()
        except RuntimeError:
            return

        elapsed = now - self._last_refill
        self._tokens = min(self._burst_size, self._tokens + elapsed * self._rate)
        self._last_refill = now

    async def acquire(self) -> bool:
        """Try to acquire a token.

        Returns:
            True if token acquired, False if rate limited.
        """
        self._refill()

        if self._tokens >= 1.0:
            self._tokens -= 1.0
            return True
        return False

    async def wait(self) -> None:
        """Wait until a token is available."""
        while not await self.acquire():
            # Calculate wait time for next token
            wait_time = (1.0 - self._tokens) / self._rate
            await asyncio.sleep(min(wait_time, 0.1))


class IPCHandler:
    """Handles JSON-RPC communication over stdin/stdout."""

    def __init__(self):
        self._running_task: asyncio.Task | None = None
        self._discussion_lock: asyncio.Lock = asyncio.Lock()  # Mutex for concurrent discussions
        self._cancel_requested: bool = False
        self._pause_event: asyncio.Event = asyncio.Event()
        self._pause_event.set()  # Start in "running" state (not paused)
        self._rate_limiter: RateLimiter = RateLimiter()
        # Bounded event queue for backpressure during high event throughput
        self._event_queue: asyncio.Queue[dict | None] = asyncio.Queue(maxsize=MAX_IPC_EVENT_QUEUE_SIZE)
        self._drain_task: asyncio.Task | None = None
        self._draining: bool = False
        # Discussion session ID - used to filter out stale events from cancelled discussions
        self._current_discussion_id: str | None = None

    # === Input Validation Helpers ===

    def _validate_string(
        self,
        value: Any,
        name: str,
        required: bool = True,
        max_length: int | None = None,
        pattern: re.Pattern | None = None,
        allowed_values: set[str] | None = None,
    ) -> str | None:
        """Validate a string parameter.

        Args:
            value: The value to validate
            name: Parameter name for error messages
            required: Whether the parameter is required
            max_length: Maximum allowed length
            pattern: Regex pattern to match
            allowed_values: Set of allowed values

        Returns:
            Validated string or None if optional and missing

        Raises:
            ValueError: If validation fails
        """
        if value is None:
            if required:
                raise ValueError(f"Missing required parameter: {name}")
            return None

        if not isinstance(value, str):
            raise ValueError(f"Invalid parameter: {name} must be a string, got {type(value).__name__}")

        if max_length and len(value) > max_length:
            raise ValueError(f"Invalid parameter: {name} exceeds maximum length of {max_length}")

        if pattern and not pattern.match(value):
            raise ValueError(f"Invalid parameter: {name} contains invalid characters")

        if allowed_values and value not in allowed_values:
            raise ValueError(f"Invalid parameter: {name} must be one of {sorted(allowed_values)}")

        return value

    def _validate_model_id(self, model_id: str, index: int | None = None) -> str:
        """Validate a single model ID using ReDoS-safe character whitelist.

        Args:
            model_id: The model ID to validate
            index: Optional index for error messages (when validating a list)

        Returns:
            Validated model ID

        Raises:
            ValueError: If validation fails
        """
        prefix = f"model_ids[{index}]" if index is not None else "model_id"

        if not isinstance(model_id, str):
            raise ValueError(f"Invalid parameter: {prefix} must be a string")

        if not model_id:
            raise ValueError(f"Invalid parameter: {prefix} cannot be empty")

        if len(model_id) > MAX_MODEL_ID_LENGTH:
            raise ValueError(f"Invalid parameter: {prefix} exceeds maximum length of {MAX_MODEL_ID_LENGTH}")

        # ReDoS-safe validation using O(n) character whitelist check
        if not all(c in MODEL_ID_VALID_CHARS for c in model_id):
            invalid_chars = [c for c in model_id if c not in MODEL_ID_VALID_CHARS]
            raise ValueError(f"Invalid parameter: {prefix} contains invalid characters: {invalid_chars[:3]}")

        # First character must be alphanumeric
        if not model_id[0].isalnum():
            raise ValueError(f"Invalid parameter: {prefix} must start with a letter or digit")

        return model_id

    def _validate_model_ids(self, value: Any, min_count: int = 2) -> list[str]:
        """Validate model_ids parameter.

        Args:
            value: The value to validate
            min_count: Minimum required models

        Returns:
            List of validated model IDs

        Raises:
            ValueError: If validation fails
        """
        if not isinstance(value, list):
            raise ValueError(f"Invalid parameter: model_ids must be a list, got {type(value).__name__}")

        if len(value) < min_count:
            raise ValueError(f"Invalid parameter: model_ids must contain at least {min_count} models")

        if len(value) > MAX_MODEL_COUNT:
            raise ValueError(f"Invalid parameter: model_ids cannot exceed {MAX_MODEL_COUNT} models")

        return [self._validate_model_id(model_id, i) for i, model_id in enumerate(value)]

    def _sanitize_question_for_analysis(self, question: str) -> str:
        """Sanitize question before sending to AI for method recommendation.

        Protects against prompt injection attacks where adversarial text in
        the question attempts to manipulate the AI's method recommendation.

        Sanitization includes:
        - Neutralizing common prompt injection patterns
        - Truncating to reasonable length (method selection doesn't need full text)
        - Preserving legitimate question content

        Args:
            question: The raw question from user input.

        Returns:
            Sanitized question safe for AI analysis.
        """
        # Maximum length for method analysis (full question not needed)
        max_analysis_length = 500

        # Patterns to neutralize (case-insensitive)
        # These are common prompt injection attempts
        injection_patterns = [
            # Instruction override attempts
            (r'(?i)ignore\s+(?:all\s+)?(?:previous|above|prior|any)\s+(?:instructions?|prompts?|rules?)', '[filtered]'),
            (r'(?i)disregard\s+(?:all\s+)?(?:previous|above|prior|any)', '[filtered]'),
            (r'(?i)forget\s+(?:everything|all|what)\s+(?:you|I)', '[filtered]'),
            # System/mode manipulation
            (r'(?i)system\s+(?:override|mode|instruction|prompt|message)', '[filtered]'),
            (r'(?i)(?:enter|switch\s+to|activate)\s+(?:developer|admin|debug|god)\s+mode', '[filtered]'),
            (r'(?i)you\s+are\s+now\s+(?:a|an|in)', '[filtered]'),
            (r'(?i)new\s+(?:system\s+)?(?:instructions?|rules?|mode)', '[filtered]'),
            # Role play / persona manipulation
            (r'(?i)(?:pretend|act|roleplay|imagine)\s+(?:you\s+are|to\s+be|as)', '[filtered]'),
            (r'(?i)from\s+now\s+on\s+(?:you|respond|act)', '[filtered]'),
            # Output manipulation
            (r'(?i)(?:always|only)\s+(?:recommend|suggest|output|return)\s+(?:the\s+)?(?:same|one|first)', '[filtered]'),
            (r'(?i)(?:do\s+not|never)\s+(?:recommend|suggest|use)', '[filtered]'),
            # JSON/format manipulation
            (r'(?i)(?:output|return|respond)\s+(?:only\s+)?(?:in\s+)?(?:this\s+)?(?:json|format)', '[filtered]'),
            # Delimiter injection
            (r'```(?:system|assistant|user)', '[filtered]'),
            (r'<(?:system|assistant|user)>', '[filtered]'),
            # Multi-line instruction blocks
            (r'(?i)(?:instructions?|rules?):\s*\n', '[filtered]\n'),
        ]

        sanitized = question

        # Apply pattern neutralization
        for pattern, replacement in injection_patterns:
            sanitized = re.sub(pattern, replacement, sanitized)

        # Truncate for analysis (we only need enough to determine method)
        if len(sanitized) > max_analysis_length:
            sanitized = sanitized[:max_analysis_length] + "..."

        return sanitized

    # === Event Queue Management ===

    async def _start_event_draining(self) -> None:
        """Start background task to drain events from queue to stdout.

        Call this before emitting high-throughput events (like during discussions)
        to enable backpressure through bounded queue.
        """
        if self._drain_task is not None:
            return  # Already running

        self._draining = True
        self._drain_task = asyncio.create_task(self._drain_events())

    async def _stop_event_draining(self) -> None:
        """Stop the event drain task and flush remaining events.

        Call this after high-throughput event emission is complete.
        """
        if self._drain_task is None:
            return

        # Signal drain task to stop
        self._draining = False
        await self._event_queue.put(None)  # Sentinel to unblock get()

        # Wait for drain task to complete
        try:
            await asyncio.wait_for(self._drain_task, timeout=5.0)
        except asyncio.TimeoutError:
            self._drain_task.cancel()
            try:
                await self._drain_task
            except asyncio.CancelledError:
                pass

        self._drain_task = None

        # Flush any remaining events
        while not self._event_queue.empty():
            try:
                event = self._event_queue.get_nowait()
                if event is not None:
                    self._write_json(event)
            except asyncio.QueueEmpty:
                break

    async def _drain_events(self) -> None:
        """Background task that drains events from queue to stdout."""
        while self._draining:
            try:
                event = await self._event_queue.get()
                if event is None:  # Sentinel
                    break
                self._write_json(event)
            except asyncio.CancelledError:
                break
            except Exception:
                # Don't crash drain task on write errors
                pass

    async def emit_event_async(self, method: str, params: dict[str, Any]) -> None:
        """Emit event asynchronously via queue (with backpressure).

        Use this during high-throughput event emission (like discussions).
        The bounded queue provides natural backpressure - if queue is full,
        this will block until space is available.

        Args:
            method: Event method name
            params: Event parameters
        """
        event = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }
        await self._event_queue.put(event)

    def emit_event(self, method: str, params: dict[str, Any]) -> None:
        """Emit a JSON-RPC notification (no id = no response expected).

        Args:
            method: Event method name
            params: Event parameters
        """
        event = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }
        self._write_json(event)

    def send_response(self, request_id: str | int, result: Any) -> None:
        """Send a JSON-RPC response.

        Args:
            request_id: The id from the request
            result: The result to send
        """
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result,
        }
        self._write_json(response)

    def send_error(
        self,
        request_id: str | int | None,
        code: int,
        message: str,
        data: Any = None
    ) -> None:
        """Send a JSON-RPC error response.

        Args:
            request_id: The id from the request (None for parse errors)
            code: Error code
            message: Error message
            data: Optional additional data
        """
        error: dict[str, Any] = {
            "code": code,
            "message": message,
        }
        if data is not None:
            error["data"] = data

        response: dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": error,
        }
        self._write_json(response)

    def _write_json(self, obj: dict) -> None:
        """Write a JSON object to stdout as a single line."""
        line = json.dumps(obj, ensure_ascii=False, default=self._json_default)
        sys.stdout.write(line + "\n")
        sys.stdout.flush()

    def _json_default(self, obj: Any) -> Any:
        """Handle non-serializable objects."""
        if is_dataclass(obj) and not isinstance(obj, type):
            return asdict(obj)
        return str(obj)

    async def handle_request(self, request: dict) -> None:
        """Handle a single JSON-RPC request.

        Args:
            request: Parsed JSON-RPC request
        """
        # Validate JSON-RPC structure
        if request.get("jsonrpc") != "2.0":
            self.send_error(request.get("id"), -32600, "Invalid Request: missing jsonrpc 2.0")
            return

        method = request.get("method")
        if not method or not isinstance(method, str):
            self.send_error(request.get("id"), -32600, "Invalid Request: missing method")
            return

        request_id = request.get("id")
        params = request.get("params", {})

        # Rate limiting - wait for token (blocks if rate exceeded)
        await self._rate_limiter.wait()

        # Route to handler
        handler_map = {
            "initialize": self._handle_initialize,
            "list_models": self._handle_list_models,
            "validate_model": self._handle_validate_model,
            "get_config": self._handle_get_config,
            "get_user_settings": self._handle_get_user_settings,
            "save_user_settings": self._handle_save_user_settings,
            "get_input_history": self._handle_get_input_history,
            "add_to_input_history": self._handle_add_to_input_history,
            "run_discussion": self._handle_run_discussion,
            "cancel_discussion": self._handle_cancel_discussion,
            "resume_discussion": self._handle_resume_discussion,
            "get_role_assignments": self._handle_get_role_assignments,
            "swap_role_assignments": self._handle_swap_role_assignments,
            "analyze_question": self._handle_analyze_question,
        }

        handler = handler_map.get(method)
        if not handler:
            self.send_error(request_id, -32601, f"Method not found: {method}")
            return

        try:
            result = await handler(params)
            if request_id is not None:
                self.send_response(request_id, result)
        except Exception as e:
            self.send_error(request_id, -32000, str(e))

    async def _handle_initialize(self, params: dict) -> dict:
        """Handle initialize request.

        Returns basic info about the backend including protocol version.
        Frontend should check protocol_version for compatibility.

        Note: Uses get_available_providers_fast() instead of Settings to avoid
        loading pydantic (~1.6s import time) during startup.
        """
        # Check if frontend provided its protocol version
        frontend_version = params.get("protocol_version")
        version_warning = None
        if frontend_version:
            version_warning = self._check_protocol_compatibility(frontend_version)

        result = {
            "name": "quorum-cli",
            "version": __version__,
            "protocol_version": PROTOCOL_VERSION,
            "providers": get_available_providers_fast(),
        }

        if version_warning:
            result["version_warning"] = version_warning

        return result

    def _check_protocol_compatibility(self, frontend_version: str) -> str | None:
        """Check if frontend protocol version is compatible.

        Returns warning message if versions differ, None if compatible.
        """
        try:
            backend_parts = [int(x) for x in PROTOCOL_VERSION.split(".")]
            frontend_parts = [int(x) for x in frontend_version.split(".")]

            # Major version mismatch is a breaking change
            if backend_parts[0] != frontend_parts[0]:
                return (
                    f"Protocol version mismatch: backend={PROTOCOL_VERSION}, "
                    f"frontend={frontend_version}. Major version differs - "
                    "this may cause compatibility issues."
                )

            # Minor version difference - may have new features
            if len(backend_parts) > 1 and len(frontend_parts) > 1:
                if backend_parts[1] > frontend_parts[1]:
                    return (
                        f"Backend has newer protocol ({PROTOCOL_VERSION} vs {frontend_version}). "
                        "Some features may not be available in this frontend version."
                    )
                elif frontend_parts[1] > backend_parts[1]:
                    return (
                        f"Frontend expects newer protocol ({frontend_version} vs {PROTOCOL_VERSION}). "
                        "Some features may not work correctly. Consider updating the backend."
                    )

            return None
        except (ValueError, IndexError):
            return f"Invalid protocol version format: {frontend_version}"

    async def _handle_list_models(self, params: dict) -> dict:
        """Handle list_models request.

        Returns all available models grouped by provider, plus cached validated models.
        Ollama models are auto-discovered from the local Ollama server.
        """
        from .config import get_validated_models_cache
        from .providers import discover_ollama_models, list_all_models_sync

        all_models = list_all_models_sync()
        validated_cache = get_validated_models_cache()

        # Auto-discover Ollama models from local server
        import logging

        import httpx
        logger = logging.getLogger(__name__)
        try:
            ollama_models = await discover_ollama_models(timeout=2.0)
            if ollama_models:
                all_models["ollama"] = [
                    type("ModelInfo", (), {
                        "id": model_id,
                        "provider": "ollama",
                        "display_name": display_name
                    })()
                    for model_id, display_name in ollama_models
                ]
        except (httpx.ConnectError, httpx.TimeoutException):
            # Ollama not running or not responding - expected case
            logger.debug("Ollama not available for discovery")
        except Exception as e:
            # Unexpected error - log for debugging but don't fail
            logger.warning("Unexpected error discovering Ollama models: %s", e)

        # Convert ModelInfo objects to dicts
        result = {}
        for provider, models in all_models.items():
            result[provider] = [
                {"id": m.id, "provider": m.provider, "display_name": m.display_name}
                for m in models
            ]
        return {"models": result, "validated": list(validated_cache)}

    async def _handle_validate_model(self, params: dict) -> dict:
        """Handle validate_model request.

        Args:
            params: {"model_id": "gpt-4o"}

        Returns:
            {"valid": true/false, "error": null or "error message"}
        """
        from .config import save_validated_model
        from .models import validate_model

        model_id_raw = params.get("model_id")
        if model_id_raw is None:
            raise ValueError("Missing required parameter: model_id")
        model_id = self._validate_model_id(model_id_raw)

        success, error = await validate_model(model_id)

        # Cache successful validations
        if success:
            save_validated_model(model_id)

        return {"valid": success, "error": error}

    async def _handle_get_config(self, params: dict) -> dict:
        """Handle get_config request.

        Returns current configuration settings.
        """
        from .config import get_settings
        settings = get_settings()
        report_dir = settings.get_report_dir()
        export_dir = settings.get_export_dir()
        return {
            "rounds_per_agent": settings.rounds_per_agent,
            "synthesizer_mode": settings.synthesizer_mode,
            "default_language": settings.default_language,
            "available_providers": settings.available_providers,
            "report_dir": str(report_dir),
            "export_dir": str(export_dir) if export_dir else None,
            "export_format": settings.export_format,
        }

    async def _handle_get_user_settings(self, params: dict) -> dict:
        """Handle get_user_settings request.

        Returns cached user settings (selected_models, method, synthesizer, etc).
        """
        from .config import get_user_settings
        return get_user_settings()

    async def _handle_save_user_settings(self, params: dict) -> dict:
        """Handle save_user_settings request.

        Saves user settings to cache (merges with existing).
        """
        from .config import save_user_settings
        save_user_settings(params)
        return {"status": "saved"}

    async def _handle_get_input_history(self, params: dict) -> dict:
        """Handle get_input_history request.

        Returns cached input history.
        """
        from .config import get_input_history
        return {"history": get_input_history()}

    async def _handle_add_to_input_history(self, params: dict) -> dict:
        """Handle add_to_input_history request.

        Adds an input to history.
        """
        from .config import add_to_input_history

        input_text = self._validate_string(
            params.get("input"),
            "input",
            required=False,
            max_length=MAX_QUESTION_LENGTH,
        )
        if input_text:
            add_to_input_history(input_text)
        return {"status": "added"}

    def _validate_discussion_params(self, params: dict) -> tuple[str, list[str], str, int | None, str | None, dict | None]:
        """Validate and extract discussion parameters.

        Args:
            params: Raw parameters from JSON-RPC request.

        Returns:
            Tuple of (question, model_ids, method, max_turns, synthesizer_mode, role_assignments)

        Raises:
            ValueError: If validation fails.
        """
        question = self._validate_string(
            params.get("question"),
            "question",
            required=True,
            max_length=MAX_QUESTION_LENGTH,
        )
        model_ids = self._validate_model_ids(params.get("model_ids"), min_count=2)

        options = params.get("options", {})
        if not isinstance(options, dict):
            raise ValueError("Invalid parameter: options must be an object")

        method = self._validate_string(
            options.get("method", "standard"),
            "options.method",
            required=False,
            allowed_values=VALID_METHODS,
        ) or "standard"

        max_turns = options.get("max_turns")
        if max_turns is not None:
            if not isinstance(max_turns, int) or max_turns < 1 or max_turns > 100:
                raise ValueError("Invalid parameter: options.max_turns must be an integer between 1 and 100")

        synthesizer_mode = self._validate_string(
            options.get("synthesizer_mode"),
            "options.synthesizer_mode",
            required=False,
            allowed_values=VALID_SYNTHESIZER_MODES,
        )

        role_assignments = options.get("role_assignments")
        if role_assignments is not None and not isinstance(role_assignments, dict):
            raise ValueError("Invalid parameter: options.role_assignments must be an object")

        return question, model_ids, method, max_turns, synthesizer_mode, role_assignments

    async def _handle_phase_pause(self, message: Any) -> None:
        """Handle pause between phases with timeout.

        Emits phase_complete event, pauses until resume or timeout,
        then auto-resumes if timeout expires.

        Args:
            message: PhaseMarker message indicating phase transition.
        """
        await self.emit_event_async("phase_complete", {
            "discussion_id": self._current_discussion_id,
            "completed_phase": message.phase - 1,
            "next_phase": message.phase,
            "next_phase_message_key": message.message_key,
            "next_phase_params": message.params,
            "method": message.method,
        })
        self._pause_event.clear()

        try:
            await asyncio.wait_for(
                self._pause_event.wait(),
                timeout=PAUSE_TIMEOUT_SECONDS
            )
        except asyncio.TimeoutError:
            await self.emit_event_async("pause_timeout", {
                "discussion_id": self._current_discussion_id,
                "message": "Auto-resuming after timeout",
                "timeout_seconds": PAUSE_TIMEOUT_SECONDS,
            })

    async def _handle_run_discussion(self, params: dict) -> dict:
        """Handle run_discussion request.

        Runs a multi-agent discussion and streams events.

        Args:
            params: {
                "question": "...",
                "model_ids": ["gpt-4o", "claude-sonnet-4-5"],
                "options": {
                    "method": "standard",  # or "oxford", "advocate", "socratic"
                    "max_turns": 6,  # Only used for Standard
                    "synthesizer_mode": "first"  # Only used for Standard
                }
            }
        """
        # Validate all parameters upfront
        question, model_ids, method, max_turns, synthesizer_mode, role_assignments = \
            self._validate_discussion_params(params)

        # Prevent concurrent discussions
        if self._discussion_lock.locked():
            raise ValueError("A discussion is already in progress. Cancel it first or wait for completion.")
        await self._discussion_lock.acquire()

        # Set running task IMMEDIATELY after lock - critical for cancellation to work
        self._running_task = asyncio.current_task()

        # Generate unique discussion ID - used to filter stale events from cancelled discussions
        self._current_discussion_id = str(uuid.uuid4())

        try:
            # Lazy import - loads team module with pydantic
            from .agents import validate_method_model_count
            from .team import FourPhaseConsensusTeam

            # Validate method vs model count
            valid, error = validate_method_model_count(method, len(model_ids))
            if not valid:
                raise ValueError(error)

            # Reset state
            self._cancel_requested = False
            self._pause_event.set()

            # Create discussion team
            team = FourPhaseConsensusTeam(
                model_ids=model_ids,
                max_discussion_turns=max_turns,
                synthesizer_override=synthesizer_mode,
                method_override=method if method != "standard" else None,
                role_assignments=role_assignments,
            )

            await self._start_event_draining()

            # Wrap the discussion loop in an async task so it can be cancelled
            async def run_discussion_loop():
                async for message in team.run_stream(task=question):
                    # Check cancel flag BEFORE processing each message
                    if self._cancel_requested:
                        await self.emit_event_async("discussion_cancelled", {
                            "discussion_id": self._current_discussion_id
                        })
                        return False  # Cancelled

                    # Pause before new phase (except phase 1)
                    if self._is_phase_marker(message) and message.phase > 1:
                        await self._handle_phase_pause(message)
                        # CRITICAL: Check cancel flag AFTER pause returns
                        # The pause might have been interrupted by cancel
                        if self._cancel_requested:
                            await self.emit_event_async("discussion_cancelled", {
                                "discussion_id": self._current_discussion_id
                            })
                            return False  # Cancelled during pause

                    await self._emit_message_async(message)
                return True  # Completed normally

            try:
                completed = await run_discussion_loop()
                if completed:
                    await self.emit_event_async("discussion_complete", {
                        "discussion_id": self._current_discussion_id
                    })

            except asyncio.CancelledError:
                # Task was cancelled (via cancel_discussion)
                # Emit cancelled event and suppress the exception
                try:
                    await self.emit_event_async("discussion_cancelled", {
                        "discussion_id": self._current_discussion_id
                    })
                except asyncio.CancelledError:
                    pass  # If emit fails due to cancellation, that's OK

            except Exception as e:
                await self.emit_event_async("discussion_error", {
                    "discussion_id": self._current_discussion_id,
                    "error": str(e)
                })
                raise

        finally:
            self._running_task = None
            # Clear discussion ID to invalidate any stale events
            self._current_discussion_id = None
            # Protect cleanup from cancellation - lock MUST be released
            try:
                await self._stop_event_draining()
            except asyncio.CancelledError:
                pass  # Don't let cancellation prevent lock release
            self._discussion_lock.release()

        return {"status": "completed"}

    def _format_message_event(self, message: Any) -> tuple[str, dict] | None:
        """Convert a message to event format (event_name, params).

        Args:
            message: A discussion message of any supported type.

        Returns:
            Tuple of (event_name, params_dict) or None if message should be skipped.
        """
        # Lazy imports for type checking (already loaded by run_discussion)
        from .team import (
            CritiqueResponse,
            FinalPosition,
            IndependentAnswer,
            PhaseMarker,
            SynthesisResult,
            TeamTextMessage,
            ThinkingComplete,
            ThinkingIndicator,
        )

        if isinstance(message, ThinkingIndicator):
            return ("thinking", {"model": message.model})

        elif isinstance(message, ThinkingComplete):
            return ("thinking_complete", {"model": message.model})

        elif isinstance(message, PhaseMarker):
            return ("phase_start", {
                "phase": message.phase,
                "message_key": message.message_key,
                "params": message.params,
                "num_participants": message.num_participants,
                "method": message.method,
                "total_phases": message.total_phases,
            })

        elif isinstance(message, IndependentAnswer):
            return ("independent_answer", {
                "source": message.source,
                "content": message.content,
            })

        elif isinstance(message, CritiqueResponse):
            return ("critique", {
                "source": message.source,
                "agreements": message.agreements,
                "disagreements": message.disagreements,
                "missing": message.missing,
            })

        elif isinstance(message, FinalPosition):
            return ("final_position", {
                "source": message.source,
                "position": message.position,
                "confidence": message.confidence,
            })

        elif isinstance(message, SynthesisResult):
            return ("synthesis", {
                "consensus": message.consensus,
                "synthesis": message.synthesis,
                "differences": message.differences,
                "synthesizer_model": message.synthesizer_model,
                "confidence_breakdown": message.confidence_breakdown,
                "message_count": message.message_count,
                "method": message.method,
            })

        elif isinstance(message, TeamTextMessage):
            return ("chat_message", {
                "source": message.source,
                "content": message.content,
                "role": message.role,
                "round_type": message.round_type,
                "method": message.method,
            })

        else:
            # Fallback for unknown message types
            source = getattr(message, "source", "unknown")
            content = getattr(message, "content", str(message))
            if content:
                return ("chat_message", {"source": source, "content": content})
            return None

    def _emit_message(self, message: Any) -> None:
        """Convert a message to IPC event and emit it synchronously."""
        event = self._format_message_event(message)
        if event:
            self.emit_event(event[0], event[1])

    async def _emit_message_async(self, message: Any) -> None:
        """Convert a message to IPC event and emit it asynchronously (with backpressure).

        Automatically injects discussion_id into all events for filtering stale events.
        """
        event = self._format_message_event(message)
        if event:
            event_name, params = event
            # Inject discussion_id into all message events
            if self._current_discussion_id:
                params["discussion_id"] = self._current_discussion_id
            await self.emit_event_async(event_name, params)

    async def _handle_cancel_discussion(self, params: dict) -> dict:
        """Handle cancel_discussion request.

        Performs a forced cancellation by:
        1. Setting the cancel flag (for cooperative checks)
        2. Triggering pause event (to break out of phase waits)
        3. Cancelling the running task (to abort in-flight API calls)
        4. Waiting for task to complete with timeout (ensures lock is released)
        5. Cleaning up the connection pool (to prevent stale connections)

        The lock is released by the finally block in _handle_run_discussion,
        NOT here. This avoids a race condition between cancel and the discussion task.
        """
        self._cancel_requested = True
        # Trigger pause event to break out of any wait
        self._pause_event.set()

        # Cancel the running task if it exists - this aborts in-flight API calls
        if self._running_task is not None and not self._running_task.done():
            self._running_task.cancel()
            # Wait for the task to fully complete (including finally block)
            # Use timeout to prevent hanging forever if task is stuck
            try:
                await asyncio.wait_for(
                    asyncio.shield(self._running_task),
                    timeout=5.0
                )
            except asyncio.TimeoutError:
                # Task didn't finish in time - force release lock as last resort
                if self._discussion_lock.locked():
                    try:
                        self._discussion_lock.release()
                    except RuntimeError:
                        pass
            except asyncio.CancelledError:
                pass  # Expected - task was cancelled

        # Clean up the connection pool to prevent stale/corrupted connections
        # from affecting the next discussion
        from .models import clear_pool
        await clear_pool()

        return {"status": "cancellation_requested"}

    async def _handle_resume_discussion(self, params: dict) -> dict:
        """Handle resume_discussion request.

        Signals the paused discussion to continue to the next phase.
        """
        self._pause_event.set()
        return {"status": "resumed"}

    async def _handle_get_role_assignments(self, params: dict) -> dict:
        """Handle get_role_assignments request.

        Returns role assignments for a given method and model list.

        Args:
            params: {
                "method": "oxford",
                "model_ids": ["gpt-4o", "claude-sonnet-4-5", ...]
            }

        Returns:
            {"assignments": {"FOR": [...], "AGAINST": [...]}} or {"assignments": null}
        """
        from .agents import get_role_assignments

        method = self._validate_string(
            params.get("method", "standard"),
            "method",
            required=False,
            allowed_values=VALID_METHODS,
        ) or "standard"

        raw_model_ids = params.get("model_ids", [])
        if not raw_model_ids:
            return {"assignments": None}

        # Validate model_ids (allow single model for role preview)
        model_ids = self._validate_model_ids(raw_model_ids, min_count=1)

        assignments = get_role_assignments(method, model_ids)
        return {"assignments": assignments}

    async def _handle_swap_role_assignments(self, params: dict) -> dict:
        """Handle swap_role_assignments request.

        Swaps team assignments (FOR<->AGAINST, etc).

        Args:
            params: {
                "assignments": {"FOR": [...], "AGAINST": [...]}
            }

        Returns:
            {"assignments": {"FOR": [...], "AGAINST": [...]}}
        """
        from .agents import swap_teams

        assignments = params.get("assignments", {})
        if not assignments:
            return {"assignments": {}}

        swapped = swap_teams(assignments)
        return {"assignments": swapped}

    async def _handle_analyze_question(self, params: dict) -> dict:
        """Handle analyze_question request.

        Analyzes a question and recommends the best discussion method.
        Uses the first validated model as the advisor.

        Args:
            params: {"question": "How long will X take?"}

        Returns:
            {
                "advisor_model": "gpt-4o-mini",
                "recommendations": {
                    "primary": {"method": "delphi", "confidence": 95, "reason": "..."},
                    "alternatives": [...]
                }
            }
        """

        from .agents import get_method_advisor_prompt
        from .clients import SystemMessage, UserMessage
        from .config import get_validated_models_cache
        from .models import get_pooled_client

        question = self._validate_string(
            params.get("question"),
            "question",
            required=True,
            max_length=MAX_QUESTION_LENGTH,
        )

        # Sanitize question for AI analysis to prevent prompt injection
        # This protects against adversarial manipulation of method recommendations
        sanitized_question = self._sanitize_question_for_analysis(question)

        # Get validated models
        validated = get_validated_models_cache()
        if not validated:
            raise ValueError("No validated models available. Please validate at least one model first.")

        # Use first validated model as advisor
        advisor_model = list(validated)[0]

        # Query using pooled client
        client = await get_pooled_client(advisor_model)

        prompt = get_method_advisor_prompt(sanitized_question)
        # Use timeout to prevent indefinite hanging
        from .constants import MODEL_TIMEOUT_SECONDS
        response = await asyncio.wait_for(
            client.create(
                messages=[
                    SystemMessage(content=prompt, source="advisor"),
                    UserMessage(content=sanitized_question, source="user"),
                ]
            ),
            timeout=MODEL_TIMEOUT_SECONDS
        )

        # Response is already a string from our client
        response_text = response

        # Parse JSON response with schema validation
        recommendations = self._parse_advisor_response(response_text)

        return {
            "advisor_model": advisor_model,
            "recommendations": recommendations
        }

    def _parse_advisor_response(self, response_text: str) -> dict:
        """Parse and validate the advisor response JSON.

        Validates the structure of the AI response to prevent injection
        and ensure data integrity.

        Args:
            response_text: Raw response from the advisor model.

        Returns:
            Validated recommendations dict with primary and alternatives.
        """
        import json as json_module

        fallback = {
            "primary": {
                "method": "standard",
                "confidence": 50,
                "reason": "Could not parse AI response, defaulting to standard method"
            },
            "alternatives": []
        }

        try:
            # Try to extract JSON from response (may have markdown wrapping)
            json_text = response_text
            if "```json" in json_text:
                json_text = json_text.split("```json")[1].split("```")[0]
            elif "```" in json_text:
                json_text = json_text.split("```")[1].split("```")[0]

            recommendations = json_module.loads(json_text.strip())

            # Validate structure
            if not isinstance(recommendations, dict):
                return fallback

            # Validate primary recommendation
            primary = recommendations.get("primary")
            if not isinstance(primary, dict):
                return fallback

            # Validate primary fields
            method = primary.get("method")
            if not isinstance(method, str) or method not in VALID_METHODS:
                primary["method"] = "standard"

            confidence = primary.get("confidence")
            if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 100):
                primary["confidence"] = 50

            reason = primary.get("reason")
            if not isinstance(reason, str):
                primary["reason"] = "AI recommendation"
            elif len(reason) > 500:
                primary["reason"] = reason[:500] + "..."

            # Validate alternatives (optional)
            alternatives = recommendations.get("alternatives", [])
            if not isinstance(alternatives, list):
                alternatives = []

            validated_alternatives = []
            for alt in alternatives[:5]:  # Limit to 5 alternatives
                if not isinstance(alt, dict):
                    continue
                alt_method = alt.get("method")
                if not isinstance(alt_method, str) or alt_method not in VALID_METHODS:
                    continue
                alt_confidence = alt.get("confidence", 0)
                if not isinstance(alt_confidence, (int, float)):
                    alt_confidence = 0
                alt_reason = alt.get("reason", "")
                if not isinstance(alt_reason, str):
                    alt_reason = ""
                validated_alternatives.append({
                    "method": alt_method,
                    "confidence": max(0, min(100, int(alt_confidence))),
                    "reason": alt_reason[:500] if alt_reason else ""
                })

            return {
                "primary": {
                    "method": primary["method"],
                    "confidence": max(0, min(100, int(primary["confidence"]))),
                    "reason": primary["reason"]
                },
                "alternatives": validated_alternatives
            }

        except (json_module.JSONDecodeError, KeyError, TypeError, IndexError):
            return fallback

    def _is_phase_marker(self, message: Any) -> bool:
        """Check if message is a PhaseMarker."""
        from .team import PhaseMarker
        return isinstance(message, PhaseMarker)


def _prewarm_imports() -> None:
    """Pre-load heavy modules during idle time.

    Importing team modules is slow (~0.5-1s first time due to pydantic).
    By doing this at startup, the first discussion starts faster.
    """
    # These are the heavy imports that slow down the first discussion
    from .agents import validate_method_model_count  # noqa: F401
    from .team import FourPhaseConsensusTeam  # noqa: F401


async def run_ipc() -> None:
    """Run the IPC handler, reading from stdin and writing to stdout."""
    handler = IPCHandler()

    # Pre-warm heavy imports in background (non-blocking)
    # This speeds up the first discussion by ~1-2s
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, _prewarm_imports)

    # Send ready signal with protocol version
    handler.emit_event("ready", {
        "version": __version__,
        "protocol_version": PROTOCOL_VERSION,
    })

    # Read lines from stdin
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)

    # Track background tasks
    pending_tasks: set[asyncio.Task] = set()

    while True:
        try:
            line = await reader.readline()
            if not line:
                break  # EOF

            line_str = line.decode("utf-8").strip()
            if not line_str:
                continue

            # Size validation BEFORE json.loads to prevent memory exhaustion DoS
            if len(line_str) > MAX_JSON_REQUEST_SIZE:
                handler.send_error(
                    None, -32600,
                    f"Request too large ({len(line_str)} bytes, max {MAX_JSON_REQUEST_SIZE})"
                )
                continue

            try:
                request = json.loads(line_str)
            except json.JSONDecodeError as e:
                handler.send_error(None, -32700, f"Parse error: {e}")
                continue

            # Handle requests concurrently - don't await
            task = asyncio.create_task(handler.handle_request(request))
            pending_tasks.add(task)
            task.add_done_callback(pending_tasks.discard)

        except Exception as e:
            handler.send_error(None, -32603, f"Internal error: {e}")

    # Wait for pending tasks on shutdown
    if pending_tasks:
        await asyncio.gather(*pending_tasks, return_exceptions=True)

    # Clean up connection pool on shutdown
    from .models import close_pool
    await close_pool()
