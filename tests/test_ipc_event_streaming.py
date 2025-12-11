"""Tests for IPC event streaming and message conversion.

Tests the event emission system and message type conversion.
These tests don't require API keys - they test the IPC layer in isolation.
"""

import json
from dataclasses import dataclass

import pytest

from quorum.ipc import IPCHandler


@pytest.fixture
def ipc_handler():
    """Create an IPCHandler instance for testing."""
    return IPCHandler()


class TestEmitEvent:
    """Tests for the emit_event method."""

    def test_emit_event_format(self, ipc_handler, capsys):
        """Test that emitted events follow JSON-RPC notification format."""
        ipc_handler.emit_event("test_event", {"key": "value"})

        captured = capsys.readouterr()
        event = json.loads(captured.out.strip())

        assert event["jsonrpc"] == "2.0"
        assert event["method"] == "test_event"
        assert event["params"] == {"key": "value"}
        assert "id" not in event  # Notifications don't have id

    def test_emit_event_no_extra_fields(self, ipc_handler, capsys):
        """Test that events don't have unexpected fields."""
        ipc_handler.emit_event("event", {"data": 123})

        captured = capsys.readouterr()
        event = json.loads(captured.out.strip())

        # Should only have jsonrpc, method, params
        assert set(event.keys()) == {"jsonrpc", "method", "params"}

    def test_emit_event_newline_delimited(self, ipc_handler, capsys):
        """Test that events are newline-delimited (NDJSON)."""
        ipc_handler.emit_event("event1", {"a": 1})
        ipc_handler.emit_event("event2", {"b": 2})

        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")

        assert len(lines) == 2
        # Each line should be valid JSON
        for line in lines:
            json.loads(line)

    def test_emit_event_unicode(self, ipc_handler, capsys):
        """Test that unicode characters are preserved in events."""
        ipc_handler.emit_event("test", {"message": "Hello 世界 🌍"})

        captured = capsys.readouterr()
        event = json.loads(captured.out.strip())

        assert event["params"]["message"] == "Hello 世界 🌍"


class TestSendResponse:
    """Tests for send_response method."""

    def test_send_response_format(self, ipc_handler, capsys):
        """Test that responses have correct JSON-RPC format."""
        ipc_handler.send_response(1, {"status": "ok"})

        captured = capsys.readouterr()
        response = json.loads(captured.out.strip())

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert response["result"] == {"status": "ok"}
        assert "error" not in response


class TestEventTypes:
    """Tests for specific event types."""

    def test_phase_start_event(self, ipc_handler, capsys):
        """Test phase_start event emission."""
        ipc_handler.emit_event("phase_start", {
            "phase": 1,
            "message": "Phase 1 begins",
            "num_participants": 3,
            "method": "oxford",
            "total_phases": 4,
        })

        captured = capsys.readouterr()
        event = json.loads(captured.out.strip())

        assert event["method"] == "phase_start"
        assert event["params"]["phase"] == 1
        assert event["params"]["message"] == "Phase 1 begins"
        assert event["params"]["num_participants"] == 3
        assert event["params"]["method"] == "oxford"
        assert event["params"]["total_phases"] == 4

    def test_independent_answer_event(self, ipc_handler, capsys):
        """Test independent_answer event emission."""
        ipc_handler.emit_event("independent_answer", {
            "source": "gpt-4",
            "content": "My independent analysis is...",
        })

        captured = capsys.readouterr()
        event = json.loads(captured.out.strip())

        assert event["method"] == "independent_answer"
        assert event["params"]["source"] == "gpt-4"
        assert event["params"]["content"] == "My independent analysis is..."

    def test_critique_event(self, ipc_handler, capsys):
        """Test critique event emission."""
        ipc_handler.emit_event("critique", {
            "source": "claude",
            "agreements": "We agree on X",
            "disagreements": "I disagree on Y",
            "missing": "Missing consideration of Z",
        })

        captured = capsys.readouterr()
        event = json.loads(captured.out.strip())

        assert event["method"] == "critique"
        assert event["params"]["source"] == "claude"
        assert event["params"]["agreements"] == "We agree on X"
        assert event["params"]["disagreements"] == "I disagree on Y"
        assert event["params"]["missing"] == "Missing consideration of Z"

    def test_final_position_event(self, ipc_handler, capsys):
        """Test final_position event emission."""
        ipc_handler.emit_event("final_position", {
            "source": "gpt-4",
            "position": "My final answer is 42",
            "confidence": "HIGH",
        })

        captured = capsys.readouterr()
        event = json.loads(captured.out.strip())

        assert event["method"] == "final_position"
        assert event["params"]["source"] == "gpt-4"
        assert event["params"]["position"] == "My final answer is 42"
        assert event["params"]["confidence"] == "HIGH"

    def test_synthesis_event(self, ipc_handler, capsys):
        """Test synthesis event emission."""
        ipc_handler.emit_event("synthesis", {
            "consensus": "YES",
            "synthesis": "The consensus is...",
            "differences": "Minor differences on timing",
            "synthesizer_model": "gpt-4",
            "confidence_breakdown": {"HIGH": 2, "MEDIUM": 1},
            "message_count": 15,
            "method": "standard",
        })

        captured = capsys.readouterr()
        event = json.loads(captured.out.strip())

        assert event["method"] == "synthesis"
        assert event["params"]["consensus"] == "YES"
        assert event["params"]["synthesis"] == "The consensus is..."
        assert event["params"]["differences"] == "Minor differences on timing"
        assert event["params"]["synthesizer_model"] == "gpt-4"
        assert event["params"]["confidence_breakdown"] == {"HIGH": 2, "MEDIUM": 1}
        assert event["params"]["message_count"] == 15
        assert event["params"]["method"] == "standard"

    def test_chat_message_event(self, ipc_handler, capsys):
        """Test chat_message event emission."""
        ipc_handler.emit_event("chat_message", {
            "source": "claude",
            "content": "My contribution...",
            "method": "standard",
            "role": None,
            "round_type": None,
        })

        captured = capsys.readouterr()
        event = json.loads(captured.out.strip())

        assert event["method"] == "chat_message"
        assert event["params"]["source"] == "claude"
        assert event["params"]["content"] == "My contribution..."
        assert event["params"]["method"] == "standard"

    def test_thinking_event(self, ipc_handler, capsys):
        """Test thinking event emission."""
        ipc_handler.emit_event("thinking", {"model": "gpt-4"})

        captured = capsys.readouterr()
        event = json.loads(captured.out.strip())

        assert event["method"] == "thinking"
        assert event["params"]["model"] == "gpt-4"


class TestControlEvents:
    """Tests for discussion control events."""

    def test_phase_complete_event(self, ipc_handler, capsys):
        """Test that phase_complete events have correct format."""
        ipc_handler.emit_event("phase_complete", {
            "completed_phase": 1,
            "next_phase": 2,
            "next_phase_message": "Phase 2 begins",
            "method": "standard",
        })

        captured = capsys.readouterr()
        event = json.loads(captured.out.strip())

        assert event["method"] == "phase_complete"
        assert event["params"]["completed_phase"] == 1
        assert event["params"]["next_phase"] == 2
        assert event["params"]["next_phase_message"] == "Phase 2 begins"
        assert event["params"]["method"] == "standard"

    def test_discussion_cancelled_event(self, ipc_handler, capsys):
        """Test that discussion_cancelled event has correct format."""
        ipc_handler.emit_event("discussion_cancelled", {})

        captured = capsys.readouterr()
        event = json.loads(captured.out.strip())

        assert event["method"] == "discussion_cancelled"
        assert event["params"] == {}

    def test_discussion_error_event(self, ipc_handler, capsys):
        """Test that discussion_error event has error message."""
        ipc_handler.emit_event("discussion_error", {"error": "Something went wrong"})

        captured = capsys.readouterr()
        event = json.loads(captured.out.strip())

        assert event["method"] == "discussion_error"
        assert event["params"]["error"] == "Something went wrong"

    def test_ready_event(self, ipc_handler, capsys):
        """Test that ready event has version."""
        ipc_handler.emit_event("ready", {"version": "1.0.0"})

        captured = capsys.readouterr()
        event = json.loads(captured.out.strip())

        assert event["method"] == "ready"
        assert event["params"]["version"] == "1.0.0"

    def test_discussion_complete_event(self, ipc_handler, capsys):
        """Test discussion_complete event."""
        ipc_handler.emit_event("discussion_complete", {"messages_count": 15})

        captured = capsys.readouterr()
        event = json.loads(captured.out.strip())

        assert event["method"] == "discussion_complete"
        assert event["params"]["messages_count"] == 15


class TestJSONSerialization:
    """Tests for JSON serialization edge cases."""

    def test_dataclass_serialization(self, ipc_handler, capsys):
        """Test that dataclasses are properly serialized."""
        @dataclass
        class NestedData:
            value: int

        ipc_handler.emit_event("test", {"nested": NestedData(value=42)})

        captured = capsys.readouterr()
        event = json.loads(captured.out.strip())

        # Dataclass should be converted to dict
        assert event["params"]["nested"] == {"value": 42}

    def test_special_characters_in_content(self, ipc_handler, capsys):
        """Test that special characters are properly escaped."""
        content_with_special = 'Quote: "hello"\nNewline\tTab'
        ipc_handler.emit_event("test", {"content": content_with_special})

        captured = capsys.readouterr()
        event = json.loads(captured.out.strip())

        assert event["params"]["content"] == content_with_special

    def test_large_content(self, ipc_handler, capsys):
        """Test that large content is handled."""
        large_content = "x" * 100000
        ipc_handler.emit_event("test", {"content": large_content})

        captured = capsys.readouterr()
        event = json.loads(captured.out.strip())

        assert len(event["params"]["content"]) == 100000

    def test_nested_dict_serialization(self, ipc_handler, capsys):
        """Test nested dictionaries are serialized correctly."""
        ipc_handler.emit_event("test", {
            "level1": {
                "level2": {
                    "value": "deep"
                }
            }
        })

        captured = capsys.readouterr()
        event = json.loads(captured.out.strip())

        assert event["params"]["level1"]["level2"]["value"] == "deep"

    def test_list_serialization(self, ipc_handler, capsys):
        """Test that lists are serialized correctly."""
        ipc_handler.emit_event("test", {
            "items": ["a", "b", "c"],
            "numbers": [1, 2, 3],
        })

        captured = capsys.readouterr()
        event = json.loads(captured.out.strip())

        assert event["params"]["items"] == ["a", "b", "c"]
        assert event["params"]["numbers"] == [1, 2, 3]

    def test_boolean_serialization(self, ipc_handler, capsys):
        """Test that booleans are serialized correctly."""
        ipc_handler.emit_event("test", {"flag": True, "other": False})

        captured = capsys.readouterr()
        event = json.loads(captured.out.strip())

        assert event["params"]["flag"] is True
        assert event["params"]["other"] is False

    def test_null_serialization(self, ipc_handler, capsys):
        """Test that None is serialized as null."""
        ipc_handler.emit_event("test", {"value": None})

        captured = capsys.readouterr()
        event = json.loads(captured.out.strip())

        assert event["params"]["value"] is None
