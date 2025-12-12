"""Base class for method orchestrators with shared functionality."""

from __future__ import annotations

import asyncio
import logging
import random
import re
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator, Callable, TypeVar

from ..agents import _make_valid_identifier
from ..clients import SystemMessage, UserMessage
from ..config import get_settings
from ..constants import (
    ERROR_MESSAGE_MAX_LENGTH,
    MAX_HISTORY_TOTAL_SIZE,
    MAX_MESSAGE_SIZE,
    PHASE_TIMEOUT_SECONDS,
)
from ..models import extract_api_error, get_pooled_client, remove_from_pool
from ..providers import format_display_name

logger = logging.getLogger(__name__)

# Type variable for generic parallel phase results
T = TypeVar("T")


# =============================================================================
# Message types for discussions
# =============================================================================

@dataclass
class ThinkingIndicator:
    """Indicator that a model is thinking/generating a response."""
    model: str


@dataclass
class ThinkingComplete:
    """Indicator that a model has finished thinking."""
    model: str


@dataclass
class PhaseMarker:
    """Marker for phase transitions in the discussion."""
    phase: int  # Phase number (1-based)
    message_key: str  # Translation key for frontend
    params: dict[str, str] = field(default_factory=dict)  # Translation parameters
    num_participants: int = 0
    method: str = "standard"
    total_phases: int = 5


@dataclass
class IndependentAnswer:
    """An independent answer from Phase 1."""
    source: str
    content: str


@dataclass
class CritiqueResponse:
    """Structured critique from Phase 2."""
    source: str
    agreements: str
    disagreements: str
    missing: str
    raw_content: str = ""


@dataclass
class FinalPosition:
    """Final position with confidence from Phase 4."""
    source: str
    position: str
    confidence: str  # "HIGH", "MEDIUM", "LOW"
    raw_content: str = ""


class ConsensusStatus(Enum):
    """Status of consensus from synthesis."""
    YES = "yes"
    PARTIAL = "partial"
    NO = "no"


@dataclass
class SynthesisResult:
    """Result from synthesis phase."""
    consensus: str  # "YES", "PARTIAL", "NO" (or method-specific like "APORIA_REACHED")
    synthesis: str
    differences: str
    raw_content: str = ""
    synthesizer_model: str = ""
    positions: list[FinalPosition] = field(default_factory=list)
    confidence_breakdown: dict[str, int] = field(default_factory=dict)
    message_count: int = 0
    method: str = ""


@dataclass
class TeamTextMessage:
    """A chat message with team/role metadata for debate methods."""
    source: str
    content: str
    role: str | None = None
    round_type: str | None = None
    method: str = "standard"


# Type alias for all message types
MessageType = ThinkingIndicator | ThinkingComplete | PhaseMarker | IndependentAnswer | CritiqueResponse | TeamTextMessage | FinalPosition | SynthesisResult


# =============================================================================
# Base Method Orchestrator
# =============================================================================

class BaseMethodOrchestrator(ABC):
    """Abstract base class for method-specific orchestrators.

    Provides shared functionality:
    - Model response handling
    - Display name formatting
    - Parallel phase execution
    - Synthesis result parsing
    - Synthesizer model selection
    """

    def __init__(
        self,
        model_ids: list[str],
        max_discussion_turns: int | None = None,
        synthesizer_override: str | None = None,
        role_assignments: dict[str, list[str]] | None = None,
    ):
        """Initialize the orchestrator.

        Args:
            model_ids: List of model IDs to use.
            max_discussion_turns: Max turns for sequential phases.
            synthesizer_override: Override for synthesizer selection mode.
            role_assignments: Optional role assignments for methods.
        """
        self.model_ids = model_ids
        self.synthesizer_override = synthesizer_override
        self.role_assignments = role_assignments

        # Calculate max turns
        if max_discussion_turns is not None:
            self.max_discussion_turns = max_discussion_turns
        else:
            settings = get_settings()
            self.max_discussion_turns = settings.rounds_per_agent * len(model_ids)

        # Display names mapping
        self._display_names: dict[str, str] = {
            model_id: format_display_name(model_id)
            for model_id in model_ids
        }

        # Tracking
        self._agent_names: set[str] = set()
        self._message_count: int = 0
        self._original_task: str = ""
        self._rotation_index: int = 0
        self._synthesis_result: SynthesisResult | None = None

        # Memory management for discussion history
        self._history_size: int = 0  # Track cumulative size in characters
        self._history: deque[tuple[str, int]] = deque()  # (model_id, message_size) for LRU eviction

    @property
    @abstractmethod
    def method_name(self) -> str:
        """Return the method name (e.g., 'standard', 'oxford')."""
        ...

    @property
    @abstractmethod
    def total_phases(self) -> int:
        """Return the total number of phases for this method."""
        ...

    @abstractmethod
    async def run_stream(self, task: str) -> AsyncIterator[MessageType]:
        """Run the discussion and stream messages.

        Args:
            task: The question or problem to discuss.

        Yields:
            Various message types for each phase.
        """
        ...

    # =========================================================================
    # Display Name Helpers
    # =========================================================================

    def _display_name(self, model_id: str) -> str:
        """Get the display name for a model ID."""
        return self._display_names.get(model_id, format_display_name(model_id))

    # =========================================================================
    # Message Factory Helpers
    # =========================================================================

    def _create_phase_marker(
        self, phase: int, params: dict[str, str] | None = None
    ) -> PhaseMarker:
        """Create a PhaseMarker for the current method.

        Args:
            phase: Phase number (1-based).
            params: Optional translation parameters.

        Returns:
            PhaseMarker with method-specific attributes.
        """
        return PhaseMarker(
            phase=phase,
            message_key=f"phase.{self.method_name}.{phase}.msg",
            params=params or {},
            num_participants=len(self.model_ids),
            method=self.method_name,
            total_phases=self.total_phases,
        )

    def _create_team_message(
        self,
        model_id: str,
        content: str,
        role: str | None = None,
        round_type: str | None = None,
    ) -> TeamTextMessage:
        """Create a TeamTextMessage with method context.

        Args:
            model_id: The model that generated the message.
            content: Message content.
            role: Optional role (e.g., "FOR", "AGAINST", "ADVOCATE").
            round_type: Optional round type (e.g., "opening", "rebuttal").

        Returns:
            TeamTextMessage with method set automatically.
        """
        return TeamTextMessage(
            source=model_id,
            content=content,
            role=role,
            round_type=round_type,
            method=self.method_name,
        )

    # =========================================================================
    # Memory Management
    # =========================================================================

    def _truncate_message(self, content: str) -> str:
        """Truncate a message to the maximum allowed size.

        Messages exceeding MAX_MESSAGE_SIZE are truncated with an indicator.
        This prevents memory exhaustion from verbose AI responses.

        Args:
            content: The message content to potentially truncate.

        Returns:
            Original content if under limit, or truncated content with suffix.
        """
        if len(content) <= MAX_MESSAGE_SIZE:
            return content

        truncated = content[:MAX_MESSAGE_SIZE - 100]  # Leave room for suffix
        suffix = f"\n\n[Response truncated - exceeded {MAX_MESSAGE_SIZE} character limit]"
        logger.warning(
            "Message truncated from %d to %d characters",
            len(content),
            len(truncated) + len(suffix)
        )
        return truncated + suffix

    def _track_history_size(self, model_id: str, message_size: int) -> None:
        """Track discussion history size and evict old messages if needed.

        Implements LRU eviction to keep total history under MAX_HISTORY_TOTAL_SIZE.
        This prevents memory exhaustion during long discussions.

        Args:
            model_id: The model that generated the message.
            message_size: Size of the message in characters.
        """
        self._history.append((model_id, message_size))
        self._history_size += message_size

        # Evict oldest messages if we exceed the limit (O(1) with deque.popleft)
        while self._history_size > MAX_HISTORY_TOTAL_SIZE and self._history:
            oldest_model, oldest_size = self._history.popleft()
            self._history_size -= oldest_size
            logger.debug(
                "Evicted old message from %s (%d chars) to stay under %d total",
                oldest_model,
                oldest_size,
                MAX_HISTORY_TOTAL_SIZE,
            )

    # =========================================================================
    # Model Response Helpers
    # =========================================================================

    async def _get_model_response(
        self,
        model_id: str,
        system_prompt: str,
        user_message: str,
        timeout: float | None = None,
    ) -> str:
        """Get a response from a model with the given prompts.

        Uses the connection pool for efficient client reuse across requests.

        Args:
            model_id: The model to use.
            system_prompt: System message for the model.
            user_message: User message to send.
            timeout: Maximum time to wait (seconds). Uses config if not specified.

        Returns:
            The model's response content, or error message if failed.
        """
        if timeout is None:
            timeout = float(get_settings().model_timeout)

        try:
            # Use pooled client for connection reuse
            client = await get_pooled_client(model_id)
            response = await asyncio.wait_for(
                client.create(
                    messages=[
                        SystemMessage(content=system_prompt, source="system"),
                        UserMessage(content=user_message, source="user"),
                    ]
                ),
                timeout=timeout,
            )
            content = self._extract_response_content(response)

            # Memory management: truncate oversized messages
            content = self._truncate_message(content)

            # Track history size for LRU eviction
            self._track_history_size(model_id, len(content))

            return content

        except asyncio.TimeoutError:
            error_msg = f"[Timeout: {self._display_name(model_id)} did not respond within {timeout:.0f}s]"
            logger.warning("API timeout for %s after %.0fs", model_id, timeout)
            # Remove from pool on timeout - connection may be stale
            await remove_from_pool(model_id)
            return error_msg

        except Exception as e:
            error_str = str(e)
            logger.error("API error for %s: %s", model_id, error_str, exc_info=True)
            short_error = error_str[:200] if len(error_str) > 200 else error_str
            # Remove from pool on error - connection may be broken
            await remove_from_pool(model_id)
            return f"[API Error: {short_error}]"

    def _extract_response_content(self, response: Any) -> str:
        """Extract text content from a model response."""
        if hasattr(response, "content"):
            content = response.content
            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                text_parts = []
                for part in content:
                    if hasattr(part, "text"):
                        text_parts.append(part.text)
                    elif isinstance(part, str):
                        text_parts.append(part)
                return "\n".join(text_parts)
        return str(response)

    # =========================================================================
    # Parallel Phase Execution
    # =========================================================================

    async def _run_parallel_phase(
        self,
        prompt_builder: Callable[[str], str],
        user_message: str,
        timeout: float = PHASE_TIMEOUT_SECONDS,
    ) -> dict[str, str]:
        """Run all models in parallel and return responses.

        Args:
            prompt_builder: Function that takes model_id and returns system prompt.
            user_message: User message to send to all models.
            timeout: Maximum time for entire phase (seconds).

        Returns:
            Dict mapping agent_name to response content.
        """
        async def get_response(model_id: str) -> tuple[str, str]:
            agent_name = _make_valid_identifier(model_id)
            try:
                prompt = prompt_builder(model_id)
                response = await self._get_model_response(model_id, prompt, user_message)
                return (agent_name, response)
            except Exception as e:
                logger.warning("Error getting response from %s: %s", model_id, e)
                return (agent_name, f"[Error: {extract_api_error(e)}]")

        tasks = [get_response(model_id) for model_id in self.model_ids]

        try:
            # Add phase-level timeout to prevent indefinite blocking
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            logger.error("Phase timeout after %.0fs - some models did not respond", timeout)
            # Return partial results for models that completed
            results = []
            for i, model_id in enumerate(self.model_ids):
                agent_name = _make_valid_identifier(model_id)
                results.append((agent_name, f"[Phase timeout: {timeout:.0f}s]"))
            return dict(results)

        # Filter out any BaseException results (shouldn't happen with inner try/except, but be safe)
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, BaseException):
                model_id = self.model_ids[i]
                agent_name = _make_valid_identifier(model_id)
                logger.error("Unexpected exception in parallel phase for %s: %s", model_id, result)
                valid_results.append((agent_name, f"[Error: {str(result)[:ERROR_MESSAGE_MAX_LENGTH]}]"))
            else:
                valid_results.append(result)

        return dict(valid_results)

    # =========================================================================
    # Synthesizer Selection
    # =========================================================================

    def _get_synthesizer_model(self) -> str:
        """Get the model to use for synthesis.

        Standard method uses config (first/random/rotate).
        Other methods always use first model.

        Returns:
            Model ID to use for synthesis.
        """
        # Non-standard methods always use first model
        if self.method_name != "standard":
            return self.model_ids[0]

        # Standard method: use config or override
        if self.synthesizer_override:
            mode = self.synthesizer_override
        else:
            settings = get_settings()
            mode = settings.synthesizer_mode

        if mode == "random":
            return random.choice(self.model_ids)
        elif mode == "rotate":
            model = self.model_ids[self._rotation_index % len(self.model_ids)]
            self._rotation_index += 1
            return model
        else:  # "first" or default
            return self.model_ids[0]

    # =========================================================================
    # Synthesis Parsing
    # =========================================================================

    def _parse_synthesis(
        self,
        content: str,
        synthesizer_model: str,
        method: str = "standard",
        positions: list[FinalPosition] | None = None,
        confidence_breakdown: dict[str, int] | None = None,
    ) -> SynthesisResult:
        """Parse the synthesis response from the model.

        Handles different formats:
        - Standard: CONSENSUS/SYNTHESIS/DIFFERENCES
        - Oxford: FOR/AGAINST/PARTIAL
        - Socratic: APORIA_REACHED/OPEN_QUESTIONS
        """
        consensus = "PARTIAL"
        synthesis = ""
        differences = ""

        # English-only patterns (AI is instructed to always use English headers)
        # Extract consensus indicator
        if method == "oxford":
            cons_match = re.search(
                r'CONSENSUS:\s*(FOR|AGAINST|PARTIAL)',
                content, re.IGNORECASE
            )
            if cons_match:
                consensus = cons_match.group(1).upper()
        else:
            cons_match = re.search(
                r'(?:CONSENSUS|APORIA_REACHED):\s*(YES|PARTIAL|NO)',
                content, re.IGNORECASE
            )
            if cons_match:
                consensus = cons_match.group(1).upper()

        # Extract SYNTHESIS
        synth_match = re.search(
            r'SYNTHESIS:\s*(.+?)(?=DIFFERENCES:|OPEN_QUESTIONS:|$)',
            content, re.DOTALL | re.IGNORECASE
        )
        if synth_match:
            synthesis = synth_match.group(1).strip()

        # Extract DIFFERENCES or OPEN_QUESTIONS
        diff_match = re.search(
            r'(?:DIFFERENCES|OPEN_QUESTIONS):\s*(.+?)(?=CONSENSUS:|APORIA_REACHED:|SYNTHESIS:|$)',
            content, re.DOTALL | re.IGNORECASE
        )
        if diff_match:
            differences = diff_match.group(1).strip()

        # Fallback
        if not synthesis:
            logger.debug(
                "Synthesis parsing fallback for %s: no SYNTHESIS section found, using raw content",
                synthesizer_model
            )
            synthesis = content

        return SynthesisResult(
            consensus=consensus,
            synthesis=synthesis,
            differences=differences if differences else "None",
            raw_content=content,
            synthesizer_model=synthesizer_model,
            positions=positions or [],
            confidence_breakdown=confidence_breakdown or {},
            message_count=self._message_count,
            method=method,
        )

    # =========================================================================
    # Formatting Helpers
    # =========================================================================

    def _format_responses(
        self,
        responses: dict[str, str],
        header_format: str = "--- {name} ---",
    ) -> str:
        """Format responses with model attribution.

        Args:
            responses: Dict mapping agent_name to response content.
            header_format: Format string for headers (uses {name}).

        Returns:
            Formatted string with all responses.
        """
        lines = []
        for model_id in self.model_ids:
            agent_name = _make_valid_identifier(model_id)
            if agent_name in responses:
                header = header_format.format(name=self._display_name(model_id))
                lines.append(f"{header}\n{responses[agent_name]}\n")
        return "\n".join(lines)

    def _count_confidence_levels(self, positions: list[FinalPosition]) -> dict[str, int]:
        """Count confidence levels from final positions."""
        confidence_count = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for pos in positions:
            conf = pos.confidence.upper()
            if conf in confidence_count:
                confidence_count[conf] += 1
        return confidence_count

    # =========================================================================
    # Result Accessors
    # =========================================================================

    def get_synthesis_result(self) -> SynthesisResult | None:
        """Get the synthesis result."""
        return self._synthesis_result
