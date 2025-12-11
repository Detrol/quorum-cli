"""Tests for consensus detection logic.

These tests are self-contained and don't require autogen dependencies.
"""

from dataclasses import dataclass

import pytest

# =============================================================================
# Mock classes (replicate minimal autogen interfaces)
# =============================================================================

@dataclass
class MockMessage:
    """Mock message for testing."""
    content: str
    source: str


@dataclass
class StopMessage:
    """Mock stop message."""
    content: str
    source: str


# =============================================================================
# Replicate ConsensusTermination logic for testing
# =============================================================================

class ConsensusTermination:
    """Termination condition that detects when all agents reach consensus."""

    def __init__(
        self,
        agent_names: list[str],
        max_messages: int = 20,
        consensus_keyword: str = "CONSENSUS:",
    ):
        self._agent_names = set(agent_names)
        self._max_messages = max_messages
        self._consensus_keyword = consensus_keyword
        self._consensus_agents: set[str] = set()
        self._message_count = 0
        self._last_consensus_message: str | None = None

    @property
    def terminated(self) -> bool:
        return (
            self._consensus_agents == self._agent_names
            or self._message_count >= self._max_messages
        )

    async def __call__(self, messages: list) -> StopMessage | None:
        self._message_count += len(messages)

        for msg in messages:
            content = getattr(msg, "content", "")
            if isinstance(content, str) and self._consensus_keyword in content:
                source = getattr(msg, "source", None)
                if source and source in self._agent_names:
                    self._consensus_agents.add(source)
                    idx = content.find(self._consensus_keyword)
                    self._last_consensus_message = content[
                        idx + len(self._consensus_keyword) :
                    ].strip()

        if self._consensus_agents == self._agent_names:
            return StopMessage(
                content=f"Consensus reached! All {len(self._agent_names)} agents agree.",
                source="ConsensusTermination",
            )

        if self._message_count >= self._max_messages:
            agreed = len(self._consensus_agents)
            total = len(self._agent_names)
            return StopMessage(
                content=f"Max messages ({self._max_messages}) reached. "
                f"{agreed}/{total} agents had reached consensus.",
                source="ConsensusTermination",
            )

        return None

    async def reset(self) -> None:
        self._consensus_agents = set()
        self._message_count = 0
        self._last_consensus_message = None


# =============================================================================
# Tests
# =============================================================================

class TestConsensusTermination:
    """Tests for ConsensusTermination class."""

    @pytest.fixture
    def agents(self):
        return ["agent_a", "agent_b", "agent_c"]

    @pytest.fixture
    def termination(self, agents):
        return ConsensusTermination(agent_names=agents, max_messages=10)

    @pytest.mark.asyncio
    async def test_initial_state(self, termination):
        """Termination should not be triggered initially."""
        assert termination.terminated is False

    @pytest.mark.asyncio
    async def test_single_consensus(self, termination):
        """Single agent consensus should not trigger termination."""
        messages = [MockMessage("CONSENSUS: I agree", "agent_a")]
        result = await termination(messages)
        assert result is None
        assert termination.terminated is False

    @pytest.mark.asyncio
    async def test_partial_consensus(self, termination):
        """Two of three agents should not trigger termination."""
        messages = [
            MockMessage("CONSENSUS: I agree", "agent_a"),
            MockMessage("CONSENSUS: Me too", "agent_b"),
        ]
        result = await termination(messages)
        assert result is None
        assert termination.terminated is False

    @pytest.mark.asyncio
    async def test_full_consensus(self, termination):
        """All agents reaching consensus should trigger termination."""
        messages = [
            MockMessage("CONSENSUS: I agree", "agent_a"),
            MockMessage("CONSENSUS: Me too", "agent_b"),
            MockMessage("CONSENSUS: Agreed", "agent_c"),
        ]
        result = await termination(messages)
        assert result is not None
        assert "Consensus reached" in result.content
        assert termination.terminated is True

    @pytest.mark.asyncio
    async def test_consensus_in_multiple_batches(self, termination):
        """Consensus detection should work across multiple message batches."""
        await termination([MockMessage("CONSENSUS: I agree", "agent_a")])
        assert termination.terminated is False

        await termination([MockMessage("CONSENSUS: Me too", "agent_b")])
        assert termination.terminated is False

        result = await termination([MockMessage("CONSENSUS: Agreed", "agent_c")])
        assert result is not None
        assert termination.terminated is True

    @pytest.mark.asyncio
    async def test_max_messages(self, termination):
        """Max messages should trigger termination."""
        messages = [MockMessage(f"Message {i}", "agent_a") for i in range(10)]
        result = await termination(messages)
        assert result is not None
        assert "Max messages" in result.content
        assert termination.terminated is True

    @pytest.mark.asyncio
    async def test_max_messages_with_partial_consensus(self, termination):
        """Max messages with partial consensus should report count."""
        await termination([MockMessage("CONSENSUS: I agree", "agent_a")])

        more_messages = [MockMessage(f"Msg {i}", "agent_b") for i in range(9)]
        result = await termination(more_messages)
        assert result is not None
        assert "1/3" in result.content

    @pytest.mark.asyncio
    async def test_unknown_source_ignored(self, termination):
        """Messages from unknown sources should be ignored."""
        messages = [MockMessage("CONSENSUS: I agree", "unknown_agent")]
        await termination(messages)
        assert termination.terminated is False

    @pytest.mark.asyncio
    async def test_no_consensus_keyword(self, termination):
        """Messages without consensus keyword should not count."""
        messages = [
            MockMessage("I agree with you", "agent_a"),
            MockMessage("Me too", "agent_b"),
            MockMessage("Sounds good", "agent_c"),
        ]
        result = await termination(messages)
        assert result is None
        assert termination.terminated is False

    @pytest.mark.asyncio
    async def test_case_sensitive_consensus(self):
        """Consensus keyword is case-sensitive by default."""
        termination = ConsensusTermination(
            agent_names=["agent_a"],
            consensus_keyword="CONSENSUS:",
        )
        messages = [MockMessage("consensus: agree", "agent_a")]
        await termination(messages)
        assert termination.terminated is False

    @pytest.mark.asyncio
    async def test_reset(self, termination):
        """Reset should clear all state."""
        await termination([MockMessage("CONSENSUS: I agree", "agent_a")])

        await termination.reset()
        assert termination.terminated is False
        assert termination._message_count == 0
        assert len(termination._consensus_agents) == 0

    @pytest.mark.asyncio
    async def test_duplicate_consensus(self, termination):
        """Same agent reaching consensus multiple times should only count once."""
        messages = [
            MockMessage("CONSENSUS: First agreement", "agent_a"),
            MockMessage("CONSENSUS: Second agreement", "agent_a"),
            MockMessage("CONSENSUS: Third agreement", "agent_a"),
        ]
        await termination(messages)
        assert termination.terminated is False
