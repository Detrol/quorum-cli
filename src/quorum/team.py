"""Team orchestration for multi-agent consensus with 4-phase system.

This module provides the main entry point for discussion orchestration.
Individual method implementations are in the methods/ subpackage.

Uses lazy imports for method classes to:
1. Reduce startup time (heavy imports deferred until needed)
2. Avoid circular import risks
3. Support registry-based method dispatch
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, AsyncIterator

from .agents import _make_valid_identifier
from .config import get_settings

# Import only message types at module level (lightweight)
from .methods import (
    ConsensusStatus,
    CritiqueResponse,
    FinalPosition,
    IndependentAnswer,
    PhaseMarker,
    SynthesisResult,
    TeamTextMessage,
    ThinkingComplete,
    ThinkingIndicator,
)
from .providers import format_display_name

if TYPE_CHECKING:
    from .methods.base import BaseMethodOrchestrator


# =============================================================================
# Method Registry (Lazy Loading)
# =============================================================================

# Registry maps method names to their import paths for lazy loading
_METHOD_REGISTRY: dict[str, tuple[str, str]] = {
    "standard": ("quorum.methods.standard", "StandardMethod"),
    "oxford": ("quorum.methods.oxford", "OxfordMethod"),
    "advocate": ("quorum.methods.advocate", "AdvocateMethod"),
    "socratic": ("quorum.methods.socratic", "SocraticMethod"),
    "delphi": ("quorum.methods.delphi", "DelphiMethod"),
    "brainstorm": ("quorum.methods.brainstorm", "BrainstormMethod"),
    "tradeoff": ("quorum.methods.tradeoff", "TradeoffMethod"),
}

# Cache for loaded method classes
_method_cache: dict[str, type] = {}


def _get_method_class(method_name: str) -> type:
    """Lazily load and return a method orchestrator class.

    Args:
        method_name: Name of the method (e.g., 'standard', 'oxford').

    Returns:
        The method class.

    Raises:
        ValueError: If method_name is not in registry.
    """
    if method_name in _method_cache:
        return _method_cache[method_name]

    if method_name not in _METHOD_REGISTRY:
        valid_methods = ", ".join(sorted(_METHOD_REGISTRY.keys()))
        raise ValueError(f"Unknown method: {method_name}. Valid methods: {valid_methods}")

    module_path, class_name = _METHOD_REGISTRY[method_name]

    # Lazy import
    import importlib
    module = importlib.import_module(module_path)
    method_class = getattr(module, class_name)

    # Cache for future use
    _method_cache[method_name] = method_class
    return method_class

# Re-export message types for backward compatibility
__all__ = [
    "FourPhaseConsensusTeam",
    "ThinkingIndicator",
    "ThinkingComplete",
    "PhaseMarker",
    "IndependentAnswer",
    "CritiqueResponse",
    "FinalPosition",
    "ConsensusStatus",
    "SynthesisResult",
    "TeamTextMessage",
]


class FourPhaseConsensusTeam:
    """A team that uses 4-phase consensus for fair, unbiased discussion.

    Phase 1: Independent answers (parallel, no context of others)
    Phase 2: Structured critique (parallel, analyze all answers)
    Phase 3: Discussion (sequential, informed by critiques)
    Phase 4: Final positions with confidence (parallel)

    This class acts as a dispatcher to method-specific implementations
    in the methods/ subpackage.
    """

    def __init__(
        self,
        model_ids: list[str],
        max_discussion_turns: int | None = None,
        synthesizer_override: str | None = None,
        method_override: str | None = None,
        role_assignments: dict[str, list[str]] | None = None,
    ):
        """Initialize the four-phase consensus team.

        Args:
            model_ids: List of model IDs to use for agents.
            max_discussion_turns: Maximum turns in Phase 3 discussion.
                For Standard: If None, uses config (rounds_per_agent * num_agents).
                For other methods: Ignored (they have fixed structures).
            synthesizer_override: Override synthesizer mode for Standard method.
                Values: "first", "random", "rotate", or None (use config default).
                Ignored for other methods (they use first model).
            method_override: Override discussion method for this session.
                Values: "standard", "oxford", "advocate", "socratic",
                "delphi", "brainstorm", "tradeoff", or None.
            role_assignments: Optional role assignments for methods like Oxford.
                Dict mapping role names to lists of model IDs.
        """
        self.model_ids = model_ids
        self.synthesizer_override = synthesizer_override
        self.method_override = method_override
        self.role_assignments = role_assignments

        # Calculate max turns - only Standard uses config, others have fixed structure
        if max_discussion_turns is not None:
            self.max_discussion_turns = max_discussion_turns
        else:
            settings = get_settings()
            self.max_discussion_turns = settings.rounds_per_agent * len(model_ids)

        # Display names mapping (model_id -> human-readable name)
        self._display_names: dict[str, str] = {
            model_id: format_display_name(model_id)
            for model_id in model_ids
        }

        # Tracking
        self._agent_names: set[str] = set()
        self._original_task: str = ""

        # Storage for results (populated by method orchestrators)
        self._synthesis_result: SynthesisResult | None = None
        self._initial_responses: dict[str, str] = {}
        self._critiques: dict[str, CritiqueResponse] = {}
        self._final_positions: list[FinalPosition] = []

        # Current method orchestrator (set during run_stream)
        self._method_orchestrator: Any = None  # Type is BaseMethodOrchestrator subclass

    def _get_discussion_method(self) -> str:
        """Get the discussion method from override.

        Returns:
            Discussion method: "standard", "oxford", "advocate", "socratic",
            "delphi", "brainstorm", or "tradeoff".
        """
        return self.method_override or "standard"

    def _create_method_orchestrator(self) -> "BaseMethodOrchestrator":
        """Create the appropriate method orchestrator using the registry.

        Uses lazy loading to defer heavy imports until the method is actually used.
        This improves startup time and avoids circular import issues.

        Returns:
            A method orchestrator instance.
        """
        method = self._get_discussion_method()

        # Get the method class from registry (lazy loaded)
        method_class = _get_method_class(method)

        # Common kwargs for all methods
        kwargs = {
            "model_ids": self.model_ids,
            "max_discussion_turns": self.max_discussion_turns,
            "synthesizer_override": self.synthesizer_override,
            "role_assignments": self.role_assignments,
        }

        return method_class(**kwargs)

    async def run_stream(
        self, task: str
    ) -> AsyncIterator[ThinkingIndicator | PhaseMarker | IndependentAnswer | CritiqueResponse | TeamTextMessage | FinalPosition | SynthesisResult]:
        """Run the discussion and stream all messages.

        Dispatches to method-specific flows based on discussion_method.
        Each method has its own authentic phase structure.

        Args:
            task: The question or problem to discuss.

        Yields:
            Various message types for each phase.
        """
        self._original_task = task
        self._agent_names = {_make_valid_identifier(m) for m in self.model_ids}

        # Create the appropriate method orchestrator
        self._method_orchestrator = self._create_method_orchestrator()

        # Run the method flow and yield all messages
        async for msg in self._method_orchestrator.run_stream(task):
            yield msg

        # Copy results from the orchestrator for backward compatibility
        self._synthesis_result = self._method_orchestrator.get_synthesis_result()

        # Copy phase-specific results if available (Standard method only)
        # Use method_name property instead of isinstance to avoid import dependency
        if self._method_orchestrator.method_name == "standard":
            self._initial_responses = self._method_orchestrator.get_initial_responses()
            self._critiques = self._method_orchestrator.get_critiques()
            self._final_positions = self._method_orchestrator.get_final_positions()

    def get_synthesis_result(self) -> SynthesisResult | None:
        """Get the synthesis result from the final phase."""
        return self._synthesis_result

    def get_initial_responses(self) -> dict[str, str]:
        """Get all Phase 1 initial responses (Standard method only)."""
        return self._initial_responses.copy()

    def get_critiques(self) -> dict[str, CritiqueResponse]:
        """Get all Phase 2 critiques (Standard method only)."""
        return self._critiques.copy()

    def get_final_positions(self) -> list[FinalPosition]:
        """Get all Phase 4 final positions (Standard method only)."""
        return self._final_positions.copy()
