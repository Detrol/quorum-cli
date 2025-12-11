"""Tests for IPC discussion control (cancel, pause, resume, concurrency).

Tests the discussion lifecycle management functionality including:
- Cancellation during discussion
- Pause/resume between phases
- Concurrent discussion prevention (mutex)
- Discussion lock state management
"""

import asyncio
import json
from dataclasses import dataclass
from io import StringIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from quorum.ipc import IPCHandler


@dataclass
class MockPhaseMarker:
    """Mock PhaseMarker for testing."""
    phase: int
    message_key: str
    params: dict = None
    num_participants: int = 2
    method: str = "standard"
    total_phases: int = 5

    def __post_init__(self):
        if self.params is None:
            self.params = {}


@dataclass
class MockIndependentAnswer:
    """Mock IndependentAnswer for testing."""
    source: str
    content: str


@pytest.fixture
def ipc_handler():
    """Create an IPCHandler instance for testing."""
    return IPCHandler()


class TestCancelDiscussion:
    """Tests for cancel_discussion functionality."""

    @pytest.mark.asyncio
    async def test_cancel_sets_flag(self, ipc_handler, capsys):
        """Test that cancel_discussion sets the cancel flag."""
        assert ipc_handler._cancel_requested is False

        request = {
            "jsonrpc": "2.0",
            "method": "cancel_discussion",
            "id": 1,
            "params": {}
        }
        await ipc_handler.handle_request(request)

        assert ipc_handler._cancel_requested is True

        captured = capsys.readouterr()
        response = json.loads(captured.out.strip())
        assert response["result"]["status"] == "cancellation_requested"

    @pytest.mark.asyncio
    async def test_cancel_breaks_pause_wait(self, ipc_handler, capsys):
        """Test that cancel_discussion also sets pause event to break out of pause wait.

        This is critical: if a discussion is paused (waiting between phases),
        cancel must set the pause_event so the loop can check _cancel_requested.
        Without this, cancel during pause would leave the lock held forever.
        """
        # Simulate paused state
        ipc_handler._pause_event.clear()
        assert not ipc_handler._pause_event.is_set()

        request = {
            "jsonrpc": "2.0",
            "method": "cancel_discussion",
            "id": 1,
            "params": {}
        }
        await ipc_handler.handle_request(request)

        # Cancel should set both the flag AND the pause event
        assert ipc_handler._cancel_requested is True
        assert ipc_handler._pause_event.is_set()  # This breaks out of pause wait


class TestResumeDiscussion:
    """Tests for resume_discussion functionality."""

    @pytest.mark.asyncio
    async def test_resume_sets_event(self, ipc_handler, capsys):
        """Test that resume_discussion sets the pause event."""
        # Clear the event to simulate paused state
        ipc_handler._pause_event.clear()
        assert not ipc_handler._pause_event.is_set()

        request = {
            "jsonrpc": "2.0",
            "method": "resume_discussion",
            "id": 1,
            "params": {}
        }
        await ipc_handler.handle_request(request)

        assert ipc_handler._pause_event.is_set()

        captured = capsys.readouterr()
        response = json.loads(captured.out.strip())
        assert response["result"]["status"] == "resumed"


class TestPauseState:
    """Tests for pause state management."""

    def test_initial_pause_state_is_running(self, ipc_handler):
        """Test that IPC handler starts in running (not paused) state."""
        assert ipc_handler._pause_event.is_set()

    def test_pause_event_can_be_cleared(self, ipc_handler):
        """Test that pause event can be cleared to simulate pause."""
        ipc_handler._pause_event.clear()
        assert not ipc_handler._pause_event.is_set()


class TestConcurrentDiscussionPrevention:
    """Tests for the mutex protecting against concurrent discussions."""

    @pytest.mark.asyncio
    async def test_concurrent_discussion_rejected(self, ipc_handler, capsys):
        """Test that starting a second discussion while one is running is rejected."""
        # Simulate a locked discussion
        await ipc_handler._discussion_lock.acquire()

        try:
            request = {
                "jsonrpc": "2.0",
                "method": "run_discussion",
                "id": 1,
                "params": {
                    "question": "Test question",
                    "model_ids": ["gpt-4", "claude"]
                }
            }
            await ipc_handler.handle_request(request)

            captured = capsys.readouterr()
            response = json.loads(captured.out.strip())
            assert response["error"]["code"] == -32000
            assert "already in progress" in response["error"]["message"].lower()
        finally:
            ipc_handler._discussion_lock.release()

    @pytest.mark.asyncio
    async def test_discussion_lock_released_after_completion(self, ipc_handler):
        """Test that discussion lock is released after normal completion."""
        async def mock_stream():
            yield MockIndependentAnswer(source="model-1", content="Done")

        mock_team = MagicMock()
        mock_team.run_stream = mock_stream

        with patch("quorum.team.FourPhaseConsensusTeam", return_value=mock_team):
            with patch("quorum.agents.validate_method_model_count", return_value=(True, None)):
                request = {
                    "jsonrpc": "2.0",
                    "method": "run_discussion",
                    "id": 1,
                    "params": {
                        "question": "Test",
                        "model_ids": ["gpt-4", "claude"]
                    }
                }

                # Capture stdout to suppress output
                import sys
                old_stdout = sys.stdout
                sys.stdout = StringIO()
                try:
                    await ipc_handler.handle_request(request)
                finally:
                    sys.stdout = old_stdout

        # Lock should be released
        assert not ipc_handler._discussion_lock.locked()

    @pytest.mark.asyncio
    async def test_discussion_lock_released_after_error(self, ipc_handler):
        """Test that discussion lock is released even if discussion errors."""
        async def mock_stream_error():
            yield MockIndependentAnswer(source="model-1", content="Start")
            raise RuntimeError("Simulated API error")

        mock_team = MagicMock()
        mock_team.run_stream = mock_stream_error

        with patch("quorum.team.FourPhaseConsensusTeam", return_value=mock_team):
            with patch("quorum.agents.validate_method_model_count", return_value=(True, None)):
                request = {
                    "jsonrpc": "2.0",
                    "method": "run_discussion",
                    "id": 1,
                    "params": {
                        "question": "Test",
                        "model_ids": ["gpt-4", "claude"]
                    }
                }

                import sys
                old_stdout = sys.stdout
                sys.stdout = StringIO()
                try:
                    await ipc_handler.handle_request(request)
                finally:
                    sys.stdout = old_stdout

        # Lock should be released even after error
        assert not ipc_handler._discussion_lock.locked()


class TestDiscussionStateReset:
    """Tests for state reset at discussion start."""

    @pytest.mark.asyncio
    async def test_cancel_flag_reset_on_new_discussion(self, ipc_handler):
        """Test that cancel flag is reset when starting a new discussion."""
        # Set cancel flag from previous discussion
        ipc_handler._cancel_requested = True

        flag_was_reset = False

        async def mock_stream(task):
            nonlocal flag_was_reset
            # By this point, cancel flag should have been reset
            flag_was_reset = not ipc_handler._cancel_requested
            yield MockIndependentAnswer(source="model-1", content="Done")

        mock_team = MagicMock()
        mock_team.run_stream = mock_stream

        with patch("quorum.team.FourPhaseConsensusTeam", return_value=mock_team):
            with patch("quorum.agents.validate_method_model_count", return_value=(True, None)):
                request = {
                    "jsonrpc": "2.0",
                    "method": "run_discussion",
                    "id": 1,
                    "params": {
                        "question": "Test",
                        "model_ids": ["gpt-4", "claude"]
                    }
                }

                import sys
                old_stdout = sys.stdout
                sys.stdout = StringIO()
                try:
                    await ipc_handler.handle_request(request)
                finally:
                    sys.stdout = old_stdout

        assert flag_was_reset

    @pytest.mark.asyncio
    async def test_pause_event_reset_on_new_discussion(self, ipc_handler):
        """Test that pause event is set (not paused) when starting a new discussion."""
        # Clear pause event to simulate paused state
        ipc_handler._pause_event.clear()

        event_was_set = False

        async def mock_stream(task):
            nonlocal event_was_set
            # By this point, pause event should be set (running)
            event_was_set = ipc_handler._pause_event.is_set()
            yield MockIndependentAnswer(source="model-1", content="Done")

        mock_team = MagicMock()
        mock_team.run_stream = mock_stream

        with patch("quorum.team.FourPhaseConsensusTeam", return_value=mock_team):
            with patch("quorum.agents.validate_method_model_count", return_value=(True, None)):
                request = {
                    "jsonrpc": "2.0",
                    "method": "run_discussion",
                    "id": 1,
                    "params": {
                        "question": "Test",
                        "model_ids": ["gpt-4", "claude"]
                    }
                }

                import sys
                old_stdout = sys.stdout
                sys.stdout = StringIO()
                try:
                    await ipc_handler.handle_request(request)
                finally:
                    sys.stdout = old_stdout

        assert event_was_set


class TestDiscussionEvents:
    """Tests for discussion event emission."""

    @pytest.mark.asyncio
    async def test_discussion_complete_emitted(self, ipc_handler, capsys):
        """Test that discussion_complete event is emitted on successful completion."""
        async def mock_stream(task):
            yield MockIndependentAnswer(source="model-1", content="Done")

        mock_team = MagicMock()
        mock_team.run_stream = mock_stream

        with patch("quorum.team.FourPhaseConsensusTeam", return_value=mock_team):
            with patch("quorum.agents.validate_method_model_count", return_value=(True, None)):
                request = {
                    "jsonrpc": "2.0",
                    "method": "run_discussion",
                    "id": 1,
                    "params": {
                        "question": "Test",
                        "model_ids": ["gpt-4", "claude"]
                    }
                }
                await ipc_handler.handle_request(request)

        captured = capsys.readouterr()
        lines = [l for l in captured.out.strip().split("\n") if l]

        # Check that discussion_complete was emitted
        complete_events = [json.loads(l) for l in lines if "discussion_complete" in l]
        assert len(complete_events) >= 1

    @pytest.mark.asyncio
    async def test_discussion_error_emitted_on_exception(self, ipc_handler, capsys):
        """Test that discussion_error event is emitted when an exception occurs."""
        async def mock_stream_error(task):
            yield MockIndependentAnswer(source="model-1", content="Start")
            raise RuntimeError("Simulated error")

        mock_team = MagicMock()
        mock_team.run_stream = mock_stream_error

        with patch("quorum.team.FourPhaseConsensusTeam", return_value=mock_team):
            with patch("quorum.agents.validate_method_model_count", return_value=(True, None)):
                request = {
                    "jsonrpc": "2.0",
                    "method": "run_discussion",
                    "id": 1,
                    "params": {
                        "question": "Test",
                        "model_ids": ["gpt-4", "claude"]
                    }
                }
                await ipc_handler.handle_request(request)

        captured = capsys.readouterr()
        lines = [l for l in captured.out.strip().split("\n") if l]

        # Check that discussion_error was emitted
        error_events = [json.loads(l) for l in lines if "discussion_error" in l]
        assert len(error_events) >= 1
        assert "Simulated error" in error_events[0]["params"]["error"]


class TestForcedCancellation:
    """Tests for forced task cancellation."""

    @pytest.mark.asyncio
    async def test_lock_released_after_forced_cancellation(self, ipc_handler):
        """Test that discussion lock is released when task is forcefully cancelled.

        This tests the critical scenario where:
        1. A discussion is running (holding the lock)
        2. User presses ESC/Ctrl+R triggering cancel_discussion
        3. cancel_discussion cancels the running task
        4. Lock MUST be released so new discussion can start
        """
        discussion_started = asyncio.Event()
        keep_running = asyncio.Event()

        async def mock_stream_slow(task):
            discussion_started.set()
            yield MockIndependentAnswer(source="model-1", content="Start")
            # Simulate a long-running API call
            await keep_running.wait()
            yield MockIndependentAnswer(source="model-1", content="End")

        mock_team = MagicMock()
        mock_team.run_stream = mock_stream_slow

        with patch("quorum.team.FourPhaseConsensusTeam", return_value=mock_team):
            with patch("quorum.agents.validate_method_model_count", return_value=(True, None)):
                with patch("quorum.models.clear_pool", new_callable=AsyncMock):
                    import sys
                    old_stdout = sys.stdout
                    sys.stdout = StringIO()
                    try:
                        # Start discussion in background
                        discussion_task = asyncio.create_task(
                            ipc_handler.handle_request({
                                "jsonrpc": "2.0",
                                "method": "run_discussion",
                                "id": 1,
                                "params": {
                                    "question": "Test",
                                    "model_ids": ["gpt-4", "claude"]
                                }
                            })
                        )

                        # Wait for discussion to start
                        await asyncio.wait_for(discussion_started.wait(), timeout=2.0)

                        # Verify lock is held
                        assert ipc_handler._discussion_lock.locked()

                        # Cancel the discussion (simulates ESC press)
                        await ipc_handler.handle_request({
                            "jsonrpc": "2.0",
                            "method": "cancel_discussion",
                            "id": 2,
                            "params": {}
                        })

                        # Wait for discussion task to complete
                        try:
                            await asyncio.wait_for(discussion_task, timeout=2.0)
                        except asyncio.CancelledError:
                            pass

                    finally:
                        sys.stdout = old_stdout
                        keep_running.set()  # Cleanup

        # CRITICAL: Lock must be released after cancellation
        assert not ipc_handler._discussion_lock.locked()

    @pytest.mark.asyncio
    async def test_new_discussion_starts_after_cancellation(self, ipc_handler, capsys):
        """Test that a new discussion can start immediately after cancellation."""
        first_discussion_started = asyncio.Event()

        async def mock_stream_first(task):
            first_discussion_started.set()
            yield MockIndependentAnswer(source="model-1", content="First")
            await asyncio.sleep(10)  # Long delay - will be cancelled
            yield MockIndependentAnswer(source="model-1", content="Never reached")

        async def mock_stream_second(task):
            yield MockIndependentAnswer(source="model-1", content="Second discussion")

        call_count = 0

        def mock_team_factory(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock = MagicMock()
            if call_count == 1:
                mock.run_stream = mock_stream_first
            else:
                mock.run_stream = mock_stream_second
            return mock

        with patch("quorum.team.FourPhaseConsensusTeam", side_effect=mock_team_factory):
            with patch("quorum.agents.validate_method_model_count", return_value=(True, None)):
                with patch("quorum.models.clear_pool", new_callable=AsyncMock):
                    import sys
                    old_stdout = sys.stdout
                    sys.stdout = StringIO()
                    try:
                        # Start first discussion
                        first_task = asyncio.create_task(
                            ipc_handler.handle_request({
                                "jsonrpc": "2.0",
                                "method": "run_discussion",
                                "id": 1,
                                "params": {
                                    "question": "First",
                                    "model_ids": ["gpt-4", "claude"]
                                }
                            })
                        )

                        # Wait for first discussion to start
                        await asyncio.wait_for(first_discussion_started.wait(), timeout=2.0)

                        # Cancel it
                        await ipc_handler.handle_request({
                            "jsonrpc": "2.0",
                            "method": "cancel_discussion",
                            "id": 2,
                            "params": {}
                        })

                        # Wait for first task to finish
                        try:
                            await asyncio.wait_for(first_task, timeout=2.0)
                        except asyncio.CancelledError:
                            pass

                        # Start second discussion - should NOT get "already in progress" error
                        sys.stdout = StringIO()  # Reset output
                        await ipc_handler.handle_request({
                            "jsonrpc": "2.0",
                            "method": "run_discussion",
                            "id": 3,
                            "params": {
                                "question": "Second",
                                "model_ids": ["gpt-4", "claude"]
                            }
                        })

                        output = sys.stdout.getvalue()
                    finally:
                        sys.stdout = old_stdout

        # Second discussion should complete without "already in progress" error
        assert "already in progress" not in output.lower()
        assert call_count == 2  # Both discussions were attempted


class TestPauseTimeout:
    """Tests for pause timeout functionality."""

    @pytest.mark.asyncio
    async def test_pause_timeout_emits_event(self, ipc_handler, capsys):
        """Test that pause_timeout event is emitted after timeout."""
        # Mock PhaseMarker to trigger pause
        phase1_marker = MockPhaseMarker(phase=1, message_key="phase.standard.1.msg")
        phase2_marker = MockPhaseMarker(phase=2, message_key="phase.standard.2.msg")

        async def mock_stream(task):
            yield phase1_marker
            yield MockIndependentAnswer(source="model-1", content="Answer 1")
            yield phase2_marker  # This will trigger pause
            yield MockIndependentAnswer(source="model-1", content="Answer 2")

        mock_team = MagicMock()
        mock_team.run_stream = mock_stream

        # Mock _is_phase_marker to recognize our MockPhaseMarker
        def mock_is_phase_marker(msg):
            return isinstance(msg, MockPhaseMarker)

        with patch("quorum.team.FourPhaseConsensusTeam", return_value=mock_team):
            with patch("quorum.agents.validate_method_model_count", return_value=(True, None)):
                # Patch timeout to a very short value for testing
                with patch("quorum.ipc.PAUSE_TIMEOUT_SECONDS", 0.1):
                    ipc_handler._is_phase_marker = mock_is_phase_marker
                    request = {
                        "jsonrpc": "2.0",
                        "method": "run_discussion",
                        "id": 1,
                        "params": {
                            "question": "Test",
                            "model_ids": ["gpt-4", "claude"]
                        }
                    }
                    await ipc_handler.handle_request(request)

        captured = capsys.readouterr()
        lines = [l for l in captured.out.strip().split("\n") if l]

        # Check that pause_timeout was emitted
        timeout_events = [json.loads(l) for l in lines if "pause_timeout" in l]
        assert len(timeout_events) >= 1
        assert "timeout_seconds" in timeout_events[0]["params"]

    @pytest.mark.asyncio
    async def test_pause_timeout_continues_discussion(self, ipc_handler, capsys):
        """Test that discussion continues after pause timeout."""
        phase1_marker = MockPhaseMarker(phase=1, message_key="phase.standard.1.msg")
        phase2_marker = MockPhaseMarker(phase=2, message_key="phase.standard.2.msg")
        phase3_marker = MockPhaseMarker(phase=3, message_key="phase.standard.3.msg")

        async def mock_stream(task):
            yield phase1_marker
            yield MockIndependentAnswer(source="model-1", content="Answer 1")
            yield phase2_marker  # First pause
            yield MockIndependentAnswer(source="model-1", content="Answer 2")
            yield phase3_marker  # Second pause
            yield MockIndependentAnswer(source="model-1", content="Answer 3")

        mock_team = MagicMock()
        mock_team.run_stream = mock_stream

        # Mock _is_phase_marker to recognize our MockPhaseMarker
        def mock_is_phase_marker(msg):
            return isinstance(msg, MockPhaseMarker)

        with patch("quorum.team.FourPhaseConsensusTeam", return_value=mock_team):
            with patch("quorum.agents.validate_method_model_count", return_value=(True, None)):
                # Patch timeout to a very short value for testing
                with patch("quorum.ipc.PAUSE_TIMEOUT_SECONDS", 0.1):
                    ipc_handler._is_phase_marker = mock_is_phase_marker
                    request = {
                        "jsonrpc": "2.0",
                        "method": "run_discussion",
                        "id": 1,
                        "params": {
                            "question": "Test",
                            "model_ids": ["gpt-4", "claude"]
                        }
                    }
                    await ipc_handler.handle_request(request)

        captured = capsys.readouterr()
        lines = [l for l in captured.out.strip().split("\n") if l]

        # Check that multiple phase_complete events were emitted (discussion continued)
        phase_events = [json.loads(l) for l in lines if "phase_complete" in l]
        assert len(phase_events) >= 2  # At least 2 phase transitions

        # Check that multiple pause_timeout events were emitted
        timeout_events = [json.loads(l) for l in lines if "pause_timeout" in l]
        assert len(timeout_events) >= 2  # Each phase transition should timeout

        # Check that discussion_complete was emitted (finished successfully)
        complete_events = [json.loads(l) for l in lines if "discussion_complete" in l]
        assert len(complete_events) >= 1
