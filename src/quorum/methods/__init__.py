"""Method-specific orchestrators for Quorum discussions.

Each method implements a specific discussion format:
- StandardMethod: 5-phase consensus-seeking
- OxfordMethod: Parliamentary debate (FOR/AGAINST)
- AdvocateMethod: Devil's advocate cross-examination
- SocraticMethod: Elenchus through questioning
- DelphiMethod: Iterative anonymous estimation
- BrainstormMethod: Divergent then convergent ideation
- TradeoffMethod: Multi-criteria decision analysis

Note: Method classes are NOT imported here to avoid circular imports
and improve startup time. Use the registry in team.py for lazy loading.
Only message types (lightweight dataclasses) are exported from this module.
"""

# Export only lightweight message types - no heavy method class imports
from .base import (
    BaseMethodOrchestrator,
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

# Method classes are lazily loaded via team._get_method_class()
# DO NOT add method class imports here as it defeats lazy loading

__all__ = [
    # Base class (used for type hints and isinstance checks)
    "BaseMethodOrchestrator",
    # Message types (lightweight dataclasses)
    "ThinkingIndicator",
    "ThinkingComplete",
    "PhaseMarker",
    "IndependentAnswer",
    "CritiqueResponse",
    "FinalPosition",
    "ConsensusStatus",
    "SynthesisResult",
    "TeamTextMessage",
    # NOTE: Method classes (StandardMethod, OxfordMethod, etc.) are NOT exported.
    # They are accessed via lazy loading in team.py to:
    # 1. Reduce startup time (heavy imports deferred until method is actually used)
    # 2. Avoid circular import risks
    # 3. Support registry-based method dispatch
]
