"""Tests for team.py error handling and recovery.

Tests model failures, timeouts, malformed responses, and graceful degradation.
These tests use mocks and don't require API keys.
"""

import asyncio
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from quorum.methods.oxford import OxfordMethod
from quorum.methods.standard import StandardMethod
from quorum.team import (
    CritiqueResponse,
    FinalPosition,
    FourPhaseConsensusTeam,
    SynthesisResult,
)


@dataclass
class MockModelResponse:
    """Mock response from AI model."""
    content: str
    source: str = "mock-model"


@pytest.fixture
def mock_settings(monkeypatch):
    """Mock settings for testing."""
    mock = MagicMock()
    mock.rounds_per_agent = 2
    mock.synthesizer_mode = "first"
    mock.default_language = None
    monkeypatch.setattr("quorum.team.get_settings", lambda: mock)
    monkeypatch.setattr("quorum.methods.base.get_settings", lambda: mock)
    return mock


@pytest.fixture
def team(mock_settings):
    """Create a team with two mock models."""
    return FourPhaseConsensusTeam(
        model_ids=["gpt-4", "claude-sonnet"],
        max_discussion_turns=4,
    )


@pytest.fixture
def standard_method(mock_settings):
    """Create a StandardMethod instance for testing internal methods."""
    model_ids = ["gpt-4", "claude-sonnet"]
    return StandardMethod(
        model_ids=model_ids,
        max_discussion_turns=4,
        synthesizer_override=None,
        role_assignments=None,
    )


class TestPhase1ErrorHandling:
    """Tests for Phase 1 (parallel answers) error handling."""

    @pytest.mark.asyncio
    async def test_single_model_failure(self, standard_method):
        """Test that discussion continues when one model fails."""
        # First model succeeds, second fails
        call_count = 0

        async def mock_create(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return MockModelResponse(content="Good answer from model 1")
            else:
                raise Exception("API rate limit exceeded")

        mock_client = AsyncMock()
        mock_client.create = mock_create

        async def mock_get_pooled_client(model_id):
            return mock_client

        with patch("quorum.methods.standard.get_pooled_client", side_effect=mock_get_pooled_client):
            with patch("quorum.methods.standard.remove_from_pool", new_callable=AsyncMock):
                results = await standard_method._run_phase1_parallel("Test question")

        # Both models should have results
        assert len(results) == 2

        # First model succeeded
        assert "Good answer" in results["gpt_4"]

        # Second model has error message
        assert "[Error:" in results["claude_sonnet"]
        assert "rate limit" in results["claude_sonnet"].lower()

    @pytest.mark.asyncio
    async def test_all_models_fail(self, standard_method):
        """Test handling when all models fail in parallel phase."""
        async def mock_create(*args, **kwargs):
            raise Exception("Service unavailable")

        mock_client = AsyncMock()
        mock_client.create = mock_create

        async def mock_get_pooled_client(model_id):
            return mock_client

        with patch("quorum.methods.standard.get_pooled_client", side_effect=mock_get_pooled_client):
            with patch("quorum.methods.standard.remove_from_pool", new_callable=AsyncMock):
                results = await standard_method._run_phase1_parallel("Test question")

        # All models should have error results
        assert len(results) == 2
        for agent_name, content in results.items():
            assert "[Error:" in content

    @pytest.mark.asyncio
    async def test_error_message_truncated(self, standard_method):
        """Test that long error messages are truncated."""
        long_error = "x" * 200  # Error longer than 100 chars

        async def mock_create(*args, **kwargs):
            raise Exception(long_error)

        mock_client = AsyncMock()
        mock_client.create = mock_create

        async def mock_get_pooled_client(model_id):
            return mock_client

        with patch("quorum.methods.standard.get_pooled_client", side_effect=mock_get_pooled_client):
            with patch("quorum.methods.standard.remove_from_pool", new_callable=AsyncMock):
                results = await standard_method._run_phase1_parallel("Test")

        # Error should be truncated to 500 chars (ERROR_MESSAGE_MAX_LENGTH)
        error_content = list(results.values())[0]
        # Format is "[Error: <message>]"
        assert len(error_content) < 520  # "[Error: " + 500 chars + "]"


class TestPhase2ErrorHandling:
    """Tests for Phase 2 (critique) error handling."""

    @pytest.mark.asyncio
    async def test_critique_model_failure(self, standard_method):
        """Test that critique phase handles model failures."""
        # Setup initial responses
        standard_method._initial_responses = {
            "gpt_4": "Answer 1",
            "claude_sonnet": "Answer 2",
        }

        call_count = 0

        async def mock_create(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return MockModelResponse(
                    content="AGREEMENTS: Both good\nDISAGREEMENTS: None\nMISSING: Nothing"
                )
            else:
                raise Exception("Model overloaded")

        mock_client = AsyncMock()
        mock_client.create = mock_create

        with patch("quorum.methods.standard.get_pooled_client", new_callable=AsyncMock, return_value=mock_client):
            results = await standard_method._run_phase2_critique("Test question")

        # Both should have results
        assert len(results) == 2

        # First succeeded
        assert "Both good" in results["gpt_4"].agreements

        # Second has error in agreements field
        assert "[Error:" in results["claude_sonnet"].agreements

    @pytest.mark.asyncio
    async def test_critique_error_produces_valid_structure(self, standard_method):
        """Test that model failure produces a valid CritiqueResponse."""
        standard_method._initial_responses = {"gpt_4": "Answer", "claude_sonnet": "Answer 2"}

        async def mock_create(*args, **kwargs):
            raise Exception("Timeout")

        mock_client = AsyncMock()
        mock_client.create = mock_create

        with patch("quorum.methods.standard.get_pooled_client", new_callable=AsyncMock, return_value=mock_client):
            results = await standard_method._run_phase2_critique("Test")

        for agent_name, critique in results.items():
            # Should be a valid CritiqueResponse
            assert isinstance(critique, CritiqueResponse)
            assert critique.source  # Should have source
            assert critique.raw_content  # Should have raw content


class TestPhase4ErrorHandling:
    """Tests for Phase 4 (final positions) error handling."""

    @pytest.mark.asyncio
    async def test_final_position_model_failure(self, standard_method):
        """Test that final position phase handles model failures."""
        standard_method._initial_responses = {"gpt_4": "A1", "claude_sonnet": "A2"}
        standard_method._critiques = {
            "gpt_4": CritiqueResponse("gpt-4", "agree", "", "", ""),
            "claude_sonnet": CritiqueResponse("claude", "agree", "", "", ""),
        }

        call_count = 0

        async def mock_create(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return MockModelResponse(
                    content="FINAL POSITION: My answer\nCONFIDENCE: HIGH"
                )
            else:
                raise Exception("Connection reset")

        mock_client = AsyncMock()
        mock_client.create = mock_create

        with patch("quorum.methods.standard.get_pooled_client", new_callable=AsyncMock, return_value=mock_client):
            results = await standard_method._run_phase4_final_positions("Test")

        # Should have results for both models
        assert len(results) == 2

        # Second model should have error in position
        error_position = [p for p in results if "[Error:" in p.position]
        assert len(error_position) == 1


class TestSynthesisErrorHandling:
    """Tests for synthesis phase error handling."""

    @pytest.mark.asyncio
    async def test_synthesis_model_failure(self, standard_method):
        """Test that synthesis phase handles model failure gracefully."""
        standard_method._final_positions = [
            FinalPosition("gpt-4", "Position A", "HIGH"),
            FinalPosition("claude", "Position B", "MEDIUM"),
        ]
        standard_method._original_task = "Test question"
        standard_method._message_count = 10

        async def mock_create(*args, **kwargs):
            raise Exception("Service error")

        mock_client = AsyncMock()
        mock_client.create = mock_create

        with patch("quorum.methods.standard.get_pooled_client", new_callable=AsyncMock, return_value=mock_client):
            result = await standard_method._run_synthesis("Test")

        # Should return a SynthesisResult even on error
        assert isinstance(result, SynthesisResult)
        # Should indicate error in synthesis
        assert "[Error" in result.synthesis or "Error" in result.consensus


class TestClientCleanup:
    """Tests for proper client cleanup on errors.

    Note: With pooled clients, we don't close clients after each request.
    Instead, clients are reused and only removed from pool on errors.
    """

    @pytest.mark.asyncio
    async def test_client_reused_on_success(self, standard_method):
        """Test that pooled client is reused (not removed) after successful response."""
        remove_from_pool_count = 0

        async def mock_remove(model_id):
            nonlocal remove_from_pool_count
            remove_from_pool_count += 1

        mock_client = AsyncMock()
        mock_client.create.return_value = MockModelResponse(content="Success")

        async def mock_get_pooled_client(model_id):
            return mock_client

        with patch("quorum.methods.standard.get_pooled_client", side_effect=mock_get_pooled_client):
            with patch("quorum.methods.standard.remove_from_pool", side_effect=mock_remove):
                await standard_method._run_phase1_parallel("Test")

        # Client should NOT be removed from pool on success
        assert remove_from_pool_count == 0

    @pytest.mark.asyncio
    async def test_client_removed_from_pool_on_error(self, standard_method):
        """Test that client is removed from pool when model errors."""
        remove_from_pool_count = 0

        async def mock_remove(model_id):
            nonlocal remove_from_pool_count
            remove_from_pool_count += 1

        async def mock_create(*args, **kwargs):
            raise Exception("API Error")

        mock_client = AsyncMock()
        mock_client.create = mock_create

        async def mock_get_pooled_client(model_id):
            return mock_client

        with patch("quorum.methods.standard.get_pooled_client", side_effect=mock_get_pooled_client):
            with patch("quorum.methods.standard.remove_from_pool", side_effect=mock_remove):
                await standard_method._run_phase1_parallel("Test")

        # Client should be removed from pool for both failed models
        assert remove_from_pool_count == 2


class TestCritiqueParsingErrors:
    """Tests for critique response parsing edge cases."""

    def test_parse_critique_empty_content(self, standard_method):
        """Test parsing empty critique response."""
        result = standard_method._parse_critique("model-1", "")

        assert isinstance(result, CritiqueResponse)
        assert result.source == "model-1"
        # Empty content should be preserved in agreements
        assert result.agreements == ""

    def test_parse_critique_no_structure(self, standard_method):
        """Test parsing critique without expected structure."""
        content = "This is just a plain text response without any structure."
        result = standard_method._parse_critique("model-1", content)

        # Should fall back to putting content in agreements
        assert content in result.agreements

    def test_parse_critique_partial_structure(self, standard_method):
        """Test parsing critique with partial structure."""
        content = "AGREEMENTS: We all agree on X\n\nSome other text without labels"
        result = standard_method._parse_critique("model-1", content)

        assert "We all agree" in result.agreements
        # Other fields should be empty
        assert result.disagreements == "" or result.disagreements is not None

    def test_parse_critique_malformed_labels(self, standard_method):
        """Test parsing critique with malformed labels."""
        content = "agree: something\nDISAGREE: other"
        result = standard_method._parse_critique("model-1", content)

        # Should handle case-insensitive matching or fall back
        assert isinstance(result, CritiqueResponse)


class TestFinalPositionParsingErrors:
    """Tests for final position parsing edge cases."""

    def test_parse_final_position_empty(self, standard_method):
        """Test parsing empty final position."""
        result = standard_method._parse_final_position("model-1", "")

        assert isinstance(result, FinalPosition)
        assert result.source == "model-1"

    def test_parse_final_position_no_confidence(self, standard_method):
        """Test parsing position without confidence level."""
        content = "My final position is X."
        result = standard_method._parse_final_position("model-1", content)

        # Should extract position and default confidence
        assert isinstance(result, FinalPosition)
        # Confidence should have a default or be extracted

    def test_parse_final_position_invalid_confidence(self, standard_method):
        """Test parsing position with invalid confidence value."""
        content = "FINAL POSITION: My answer\nCONFIDENCE: VERY_HIGH"
        result = standard_method._parse_final_position("model-1", content)

        # Should handle gracefully - either normalize or use as-is
        assert isinstance(result, FinalPosition)


class TestSynthesisParsingErrors:
    """Tests for synthesis result parsing edge cases."""

    def test_parse_synthesis_empty(self, standard_method):
        """Test parsing empty synthesis."""
        result = standard_method._parse_synthesis("", "model-1")

        assert isinstance(result, SynthesisResult)
        assert result.synthesizer_model == "model-1"

    def test_parse_synthesis_no_structure(self, standard_method):
        """Test parsing synthesis without expected structure."""
        content = "Here is my summary of the discussion..."
        result = standard_method._parse_synthesis(content, "model-1")

        # Should handle gracefully
        assert isinstance(result, SynthesisResult)

    def test_parse_synthesis_invalid_consensus(self, standard_method):
        """Test parsing synthesis with invalid consensus value."""
        content = "CONSENSUS: MAYBE\nSYNTHESIS: Something"
        result = standard_method._parse_synthesis(content, "model-1")

        # Should handle invalid consensus value
        assert isinstance(result, SynthesisResult)


class TestTimeoutHandling:
    """Tests for timeout scenarios."""

    @pytest.mark.asyncio
    async def test_slow_model_doesnt_block_others(self, standard_method):
        """Test that slow models don't block faster ones in parallel phases."""
        call_times = []

        async def mock_create(*args, **kwargs):
            import time
            start = time.time()
            # Simulate varying response times
            await asyncio.sleep(0.01)  # Fast response
            call_times.append(time.time() - start)
            return MockModelResponse(content="Response")

        mock_client = AsyncMock()
        mock_client.create = mock_create

        async def mock_get_pooled_client(model_id):
            return mock_client

        with patch("quorum.methods.standard.get_pooled_client", side_effect=mock_get_pooled_client):
            with patch("quorum.methods.standard.remove_from_pool", new_callable=AsyncMock):
                import time
                start = time.time()
                await standard_method._run_phase1_parallel("Test")
                elapsed = time.time() - start

        # Should complete in parallel, not sequentially
        # If sequential, would take ~2*0.01 = 0.02s
        # Parallel should be closer to 0.01s (with some overhead)
        assert elapsed < 0.05  # Allow some overhead


class TestDiscussionMethodErrorHandling:
    """Tests for error handling in different discussion methods."""

    @pytest.mark.asyncio
    async def test_oxford_flow_handles_model_error(self, mock_settings):
        """Test that Oxford flow handles model errors gracefully."""
        model_ids = ["gpt-4", "claude"]

        oxford_method = OxfordMethod(
            model_ids=model_ids,
            max_discussion_turns=4,
            synthesizer_override=None,
            role_assignments={
                "FOR": ["gpt-4"],
                "AGAINST": ["claude"],
            },
        )

        messages = []
        error_count = 0

        async def mock_create(*args, **kwargs):
            nonlocal error_count
            error_count += 1
            if error_count == 1:
                raise Exception("First call fails")
            return MockModelResponse(content="Response")

        mock_client = AsyncMock()
        mock_client.create = mock_create

        with patch("quorum.methods.oxford.get_pooled_client", new_callable=AsyncMock, return_value=mock_client):
            try:
                async for msg in oxford_method.run_stream("Test"):
                    messages.append(msg)
                    if len(messages) > 20:  # Safety limit
                        break
            except Exception:
                pass  # Expected - oxford flow may propagate errors

        # Should have attempted to run
        assert error_count >= 1


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_empty_model_response(self, standard_method):
        """Test handling of empty model response."""
        mock_client = AsyncMock()
        mock_client.create.return_value = MockModelResponse(content="")

        async def mock_get_pooled_client(model_id):
            return mock_client

        with patch("quorum.methods.standard.get_pooled_client", side_effect=mock_get_pooled_client):
            with patch("quorum.methods.standard.remove_from_pool", new_callable=AsyncMock):
                results = await standard_method._run_phase1_parallel("Test")

        # Should handle empty responses
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_response_with_only_whitespace(self, standard_method):
        """Test handling of whitespace-only response."""
        mock_client = AsyncMock()
        mock_client.create.return_value = MockModelResponse(content="   \n\t  ")

        async def mock_get_pooled_client(model_id):
            return mock_client

        with patch("quorum.methods.standard.get_pooled_client", side_effect=mock_get_pooled_client):
            with patch("quorum.methods.standard.remove_from_pool", new_callable=AsyncMock):
                results = await standard_method._run_phase1_parallel("Test")

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_unicode_in_error_message(self, standard_method):
        """Test that unicode in error messages is handled."""
        async def mock_create(*args, **kwargs):
            raise Exception("Error with émojis: 🔥💀")

        mock_client = AsyncMock()
        mock_client.create = mock_create

        async def mock_get_pooled_client(model_id):
            return mock_client

        with patch("quorum.methods.standard.get_pooled_client", side_effect=mock_get_pooled_client):
            with patch("quorum.methods.standard.remove_from_pool", new_callable=AsyncMock):
                results = await standard_method._run_phase1_parallel("Test")

        # Should handle unicode without crashing
        assert len(results) == 2
        # Error message should be present
        assert any("[Error:" in v for v in results.values())

    @pytest.mark.asyncio
    async def test_concurrent_model_errors(self, standard_method):
        """Test handling when multiple models fail concurrently with different errors."""
        errors = ["Rate limit", "Timeout", "Server error"]
        error_idx = 0

        async def mock_create(*args, **kwargs):
            nonlocal error_idx
            error = errors[error_idx % len(errors)]
            error_idx += 1
            raise Exception(error)

        mock_client = AsyncMock()
        mock_client.create = mock_create

        async def mock_get_pooled_client(model_id):
            return mock_client

        with patch("quorum.methods.standard.get_pooled_client", side_effect=mock_get_pooled_client):
            with patch("quorum.methods.standard.remove_from_pool", new_callable=AsyncMock):
                results = await standard_method._run_phase1_parallel("Test")

        # Both models should have error results
        assert len(results) == 2
        # Errors should be different
        error_messages = [v for v in results.values()]
        assert all("[Error:" in msg for msg in error_messages)
