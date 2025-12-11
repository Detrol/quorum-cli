"""Tests for IPC error handling and input validation.

Tests JSON-RPC protocol errors, input validation, and error responses.
These tests don't require API keys - they test the IPC layer in isolation.
"""

import json
from io import StringIO
from unittest.mock import patch

import pytest

from quorum.ipc import (
    MAX_MODEL_COUNT,
    MAX_MODEL_ID_LENGTH,
    MAX_QUESTION_LENGTH,
    VALID_METHODS,
    IPCHandler,
)


@pytest.fixture
def ipc_handler():
    """Create an IPCHandler instance for testing."""
    return IPCHandler()


class TestStringValidation:
    """Tests for _validate_string helper method."""

    def test_validate_string_required_missing(self, ipc_handler):
        """Test that missing required string raises ValueError."""
        with pytest.raises(ValueError, match="Missing required parameter"):
            ipc_handler._validate_string(None, "test_param", required=True)

    def test_validate_string_optional_missing(self, ipc_handler):
        """Test that missing optional string returns None."""
        result = ipc_handler._validate_string(None, "test_param", required=False)
        assert result is None

    def test_validate_string_wrong_type(self, ipc_handler):
        """Test that non-string value raises ValueError."""
        with pytest.raises(ValueError, match="must be a string"):
            ipc_handler._validate_string(123, "test_param")

        with pytest.raises(ValueError, match="must be a string"):
            ipc_handler._validate_string(["list"], "test_param")

        with pytest.raises(ValueError, match="must be a string"):
            ipc_handler._validate_string({"dict": "value"}, "test_param")

    def test_validate_string_exceeds_max_length(self, ipc_handler):
        """Test that string exceeding max_length raises ValueError."""
        with pytest.raises(ValueError, match="exceeds maximum length"):
            ipc_handler._validate_string("a" * 101, "test_param", max_length=100)

    def test_validate_string_at_max_length(self, ipc_handler):
        """Test that string at exactly max_length is valid."""
        result = ipc_handler._validate_string("a" * 100, "test_param", max_length=100)
        assert result == "a" * 100

    def test_validate_string_invalid_pattern(self, ipc_handler):
        """Test that string not matching pattern raises ValueError."""
        import re
        pattern = re.compile(r'^[a-z]+$')
        with pytest.raises(ValueError, match="invalid characters"):
            ipc_handler._validate_string("ABC123", "test_param", pattern=pattern)

    def test_validate_string_valid_pattern(self, ipc_handler):
        """Test that string matching pattern is valid."""
        import re
        pattern = re.compile(r'^[a-z]+$')
        result = ipc_handler._validate_string("abc", "test_param", pattern=pattern)
        assert result == "abc"

    def test_validate_string_not_in_allowed_values(self, ipc_handler):
        """Test that string not in allowed_values raises ValueError."""
        with pytest.raises(ValueError, match="must be one of"):
            ipc_handler._validate_string("invalid", "method", allowed_values={"a", "b", "c"})

    def test_validate_string_in_allowed_values(self, ipc_handler):
        """Test that string in allowed_values is valid."""
        result = ipc_handler._validate_string("standard", "method", allowed_values=VALID_METHODS)
        assert result == "standard"


class TestModelIdsValidation:
    """Tests for _validate_model_ids helper method."""

    def test_validate_model_ids_not_a_list(self, ipc_handler):
        """Test that non-list value raises ValueError."""
        with pytest.raises(ValueError, match="must be a list"):
            ipc_handler._validate_model_ids("not-a-list")

        with pytest.raises(ValueError, match="must be a list"):
            ipc_handler._validate_model_ids({"dict": "value"})

    def test_validate_model_ids_too_few(self, ipc_handler):
        """Test that list with too few models raises ValueError."""
        with pytest.raises(ValueError, match="at least 2"):
            ipc_handler._validate_model_ids(["only-one"], min_count=2)

    def test_validate_model_ids_too_many(self, ipc_handler):
        """Test that list exceeding MAX_MODEL_COUNT raises ValueError."""
        models = [f"model-{i}" for i in range(MAX_MODEL_COUNT + 1)]
        with pytest.raises(ValueError, match=f"cannot exceed {MAX_MODEL_COUNT}"):
            ipc_handler._validate_model_ids(models)

    def test_validate_model_ids_non_string_item(self, ipc_handler):
        """Test that non-string model ID raises ValueError."""
        with pytest.raises(ValueError, match=r"model_ids\[1\] must be a string"):
            ipc_handler._validate_model_ids(["gpt-4", 123, "claude"])

    def test_validate_model_ids_item_too_long(self, ipc_handler):
        """Test that model ID exceeding max length raises ValueError."""
        models = ["gpt-4", "a" * (MAX_MODEL_ID_LENGTH + 1)]
        with pytest.raises(ValueError, match=r"model_ids\[1\] exceeds maximum length"):
            ipc_handler._validate_model_ids(models)

    def test_validate_model_ids_invalid_pattern(self, ipc_handler):
        """Test that model ID with invalid characters raises ValueError."""
        # Model IDs use character whitelist (MODEL_ID_VALID_CHARS) + alphanumeric first char
        with pytest.raises(ValueError, match=r"model_ids\[1\] contains invalid characters"):
            ipc_handler._validate_model_ids(["gpt-4", "model with spaces"])

        # First character must be alphanumeric
        with pytest.raises(ValueError, match=r"model_ids\[0\] must start with a letter or digit"):
            ipc_handler._validate_model_ids(["-starts-with-dash", "gpt-4"])

    def test_validate_model_ids_valid(self, ipc_handler):
        """Test that valid model IDs pass validation."""
        models = ["gpt-4o", "claude-sonnet-4-5-20250929", "gemini-2.5-pro"]
        result = ipc_handler._validate_model_ids(models)
        assert result == models

    def test_validate_model_ids_with_special_valid_chars(self, ipc_handler):
        """Test that model IDs with allowed special chars are valid."""
        # Allowed: alphanumeric, dash, dot, slash, colon, underscore
        models = ["gpt-4.1", "model:variant", "provider/model_name"]
        result = ipc_handler._validate_model_ids(models)
        assert result == models


class TestJSONRPCProtocol:
    """Tests for JSON-RPC 2.0 protocol compliance."""

    @pytest.mark.asyncio
    async def test_missing_jsonrpc_version(self, ipc_handler, capsys):
        """Test that missing jsonrpc version returns error."""
        request = {"method": "initialize", "id": 1}
        await ipc_handler.handle_request(request)

        captured = capsys.readouterr()
        response = json.loads(captured.out.strip())
        assert response["error"]["code"] == -32600
        assert "jsonrpc 2.0" in response["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_wrong_jsonrpc_version(self, ipc_handler, capsys):
        """Test that wrong jsonrpc version returns error."""
        request = {"jsonrpc": "1.0", "method": "initialize", "id": 1}
        await ipc_handler.handle_request(request)

        captured = capsys.readouterr()
        response = json.loads(captured.out.strip())
        assert response["error"]["code"] == -32600

    @pytest.mark.asyncio
    async def test_missing_method(self, ipc_handler, capsys):
        """Test that missing method returns error."""
        request = {"jsonrpc": "2.0", "id": 1}
        await ipc_handler.handle_request(request)

        captured = capsys.readouterr()
        response = json.loads(captured.out.strip())
        assert response["error"]["code"] == -32600
        assert "method" in response["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_method_not_found(self, ipc_handler, capsys):
        """Test that unknown method returns -32601 error."""
        request = {"jsonrpc": "2.0", "method": "unknown_method", "id": 1}
        await ipc_handler.handle_request(request)

        captured = capsys.readouterr()
        response = json.loads(captured.out.strip())
        assert response["error"]["code"] == -32601
        assert "not found" in response["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_notification_no_response(self, ipc_handler, capsys):
        """Test that notification (no id) doesn't send response on success."""
        with patch.object(ipc_handler, "_handle_initialize", return_value={"status": "ok"}):
            request = {"jsonrpc": "2.0", "method": "initialize"}  # No id = notification
            await ipc_handler.handle_request(request)

        # For notifications, no response should be sent on success
        captured = capsys.readouterr()
        assert captured.out == ""


class TestRunDiscussionValidation:
    """Tests for run_discussion parameter validation."""

    @pytest.mark.asyncio
    async def test_run_discussion_missing_question(self, ipc_handler, capsys):
        """Test that missing question raises error."""
        request = {
            "jsonrpc": "2.0",
            "method": "run_discussion",
            "id": 1,
            "params": {
                "model_ids": ["gpt-4", "claude"]
            }
        }
        await ipc_handler.handle_request(request)

        captured = capsys.readouterr()
        response = json.loads(captured.out.strip())
        assert response["error"]["code"] == -32000
        assert "question" in response["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_run_discussion_question_too_long(self, ipc_handler, capsys):
        """Test that question exceeding max length raises error."""
        request = {
            "jsonrpc": "2.0",
            "method": "run_discussion",
            "id": 1,
            "params": {
                "question": "x" * (MAX_QUESTION_LENGTH + 1),
                "model_ids": ["gpt-4", "claude"]
            }
        }
        await ipc_handler.handle_request(request)

        captured = capsys.readouterr()
        response = json.loads(captured.out.strip())
        assert response["error"]["code"] == -32000
        assert "maximum length" in response["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_run_discussion_invalid_method(self, ipc_handler, capsys):
        """Test that invalid method raises error."""
        request = {
            "jsonrpc": "2.0",
            "method": "run_discussion",
            "id": 1,
            "params": {
                "question": "Test question",
                "model_ids": ["gpt-4", "claude"],
                "options": {"method": "invalid_method"}
            }
        }
        await ipc_handler.handle_request(request)

        captured = capsys.readouterr()
        response = json.loads(captured.out.strip())
        assert response["error"]["code"] == -32000
        assert "must be one of" in response["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_run_discussion_invalid_synthesizer_mode(self, ipc_handler, capsys):
        """Test that invalid synthesizer_mode raises error."""
        request = {
            "jsonrpc": "2.0",
            "method": "run_discussion",
            "id": 1,
            "params": {
                "question": "Test question",
                "model_ids": ["gpt-4", "claude"],
                "options": {"synthesizer_mode": "invalid_mode"}
            }
        }
        await ipc_handler.handle_request(request)

        captured = capsys.readouterr()
        response = json.loads(captured.out.strip())
        assert response["error"]["code"] == -32000

    @pytest.mark.asyncio
    async def test_run_discussion_invalid_max_turns(self, ipc_handler):
        """Test that invalid max_turns raises error."""
        for invalid_value in [0, -1, 101, "not_a_number"]:
            handler = IPCHandler()  # Fresh handler for each
            request = {
                "jsonrpc": "2.0",
                "method": "run_discussion",
                "id": 1,
                "params": {
                    "question": "Test question",
                    "model_ids": ["gpt-4", "claude"],
                    "options": {"max_turns": invalid_value}
                }
            }

            # Capture using a buffer
            output = StringIO()
            import sys
            old_stdout = sys.stdout
            sys.stdout = output
            try:
                await handler.handle_request(request)
            finally:
                sys.stdout = old_stdout

            response = json.loads(output.getvalue().strip())
            assert response["error"]["code"] == -32000

    @pytest.mark.asyncio
    async def test_run_discussion_options_not_dict(self, ipc_handler, capsys):
        """Test that non-dict options raises error."""
        request = {
            "jsonrpc": "2.0",
            "method": "run_discussion",
            "id": 1,
            "params": {
                "question": "Test question",
                "model_ids": ["gpt-4", "claude"],
                "options": "not_a_dict"
            }
        }
        await ipc_handler.handle_request(request)

        captured = capsys.readouterr()
        response = json.loads(captured.out.strip())
        assert response["error"]["code"] == -32000
        assert "options must be an object" in response["error"]["message"].lower()


class TestValidateModelValidation:
    """Tests for validate_model parameter validation."""

    @pytest.mark.asyncio
    async def test_validate_model_missing_model_id(self, ipc_handler, capsys):
        """Test that missing model_id raises error."""
        request = {
            "jsonrpc": "2.0",
            "method": "validate_model",
            "id": 1,
            "params": {}
        }
        await ipc_handler.handle_request(request)

        captured = capsys.readouterr()
        response = json.loads(captured.out.strip())
        assert response["error"]["code"] == -32000
        assert "model_id" in response["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_validate_model_invalid_model_id_type(self, ipc_handler, capsys):
        """Test that non-string model_id raises error."""
        request = {
            "jsonrpc": "2.0",
            "method": "validate_model",
            "id": 1,
            "params": {"model_id": 123}
        }
        await ipc_handler.handle_request(request)

        captured = capsys.readouterr()
        response = json.loads(captured.out.strip())
        assert response["error"]["code"] == -32000
        assert "must be a string" in response["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_validate_model_invalid_pattern(self, ipc_handler, capsys):
        """Test that model_id with invalid chars raises error."""
        request = {
            "jsonrpc": "2.0",
            "method": "validate_model",
            "id": 1,
            "params": {"model_id": "model with spaces"}
        }
        await ipc_handler.handle_request(request)

        captured = capsys.readouterr()
        response = json.loads(captured.out.strip())
        assert response["error"]["code"] == -32000
        assert "invalid characters" in response["error"]["message"].lower()


class TestGetRoleAssignmentsValidation:
    """Tests for get_role_assignments parameter validation."""

    @pytest.mark.asyncio
    async def test_get_role_assignments_invalid_method(self, ipc_handler, capsys):
        """Test that invalid method raises error."""
        request = {
            "jsonrpc": "2.0",
            "method": "get_role_assignments",
            "id": 1,
            "params": {
                "method": "invalid_method",
                "model_ids": ["gpt-4", "claude"]
            }
        }
        await ipc_handler.handle_request(request)

        captured = capsys.readouterr()
        response = json.loads(captured.out.strip())
        assert response["error"]["code"] == -32000
        assert "must be one of" in response["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_get_role_assignments_empty_models_returns_none(self, ipc_handler, capsys):
        """Test that empty model_ids returns null assignments."""
        request = {
            "jsonrpc": "2.0",
            "method": "get_role_assignments",
            "id": 1,
            "params": {
                "method": "oxford",
                "model_ids": []
            }
        }
        await ipc_handler.handle_request(request)

        captured = capsys.readouterr()
        response = json.loads(captured.out.strip())
        assert response["result"]["assignments"] is None


class TestAddToInputHistoryValidation:
    """Tests for add_to_input_history parameter validation."""

    @pytest.mark.asyncio
    async def test_add_history_input_too_long(self, ipc_handler, capsys):
        """Test that input exceeding max length raises error."""
        request = {
            "jsonrpc": "2.0",
            "method": "add_to_input_history",
            "id": 1,
            "params": {
                "input": "x" * (MAX_QUESTION_LENGTH + 1)
            }
        }
        await ipc_handler.handle_request(request)

        captured = capsys.readouterr()
        response = json.loads(captured.out.strip())
        assert response["error"]["code"] == -32000
        assert "maximum length" in response["error"]["message"].lower()


class TestErrorResponseFormat:
    """Tests for error response formatting."""

    def test_send_error_basic(self, ipc_handler, capsys):
        """Test basic error response format."""
        ipc_handler.send_error(1, -32600, "Test error")

        captured = capsys.readouterr()
        response = json.loads(captured.out.strip())

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert response["error"]["code"] == -32600
        assert response["error"]["message"] == "Test error"
        assert "data" not in response["error"]

    def test_send_error_with_data(self, ipc_handler, capsys):
        """Test error response with additional data."""
        ipc_handler.send_error(1, -32000, "Error", data={"details": "extra info"})

        captured = capsys.readouterr()
        response = json.loads(captured.out.strip())

        assert response["error"]["data"] == {"details": "extra info"}

    def test_send_error_null_id(self, ipc_handler, capsys):
        """Test error response with null id (parse errors)."""
        ipc_handler.send_error(None, -32700, "Parse error")

        captured = capsys.readouterr()
        response = json.loads(captured.out.strip())

        assert response["id"] is None


class TestInputInjectionAttempts:
    """Tests for various input injection attack patterns."""

    @pytest.mark.asyncio
    async def test_model_id_path_traversal(self, ipc_handler, capsys):
        """Test that path traversal in model_id is rejected."""
        request = {
            "jsonrpc": "2.0",
            "method": "validate_model",
            "id": 1,
            "params": {"model_id": "../../../etc/passwd"}
        }
        await ipc_handler.handle_request(request)

        captured = capsys.readouterr()
        response = json.loads(captured.out.strip())
        assert response["error"]["code"] == -32000

    @pytest.mark.asyncio
    async def test_model_id_command_injection(self, ipc_handler):
        """Test that command injection in model_id is rejected."""
        import sys

        for payload in ["model; rm -rf /", "model | cat /etc/passwd", "model`whoami`"]:
            handler = IPCHandler()
            request = {
                "jsonrpc": "2.0",
                "method": "validate_model",
                "id": 1,
                "params": {"model_id": payload}
            }

            output = StringIO()
            old_stdout = sys.stdout
            sys.stdout = output
            try:
                await handler.handle_request(request)
            finally:
                sys.stdout = old_stdout

            response = json.loads(output.getvalue().strip())
            assert response["error"]["code"] == -32000

    @pytest.mark.asyncio
    async def test_model_ids_array_injection(self, ipc_handler, capsys):
        """Test that nested objects in model_ids are rejected."""
        request = {
            "jsonrpc": "2.0",
            "method": "run_discussion",
            "id": 1,
            "params": {
                "question": "test",
                "model_ids": ["gpt-4", {"__proto__": "injection"}]
            }
        }
        await ipc_handler.handle_request(request)

        captured = capsys.readouterr()
        response = json.loads(captured.out.strip())
        assert response["error"]["code"] == -32000
        assert "must be a string" in response["error"]["message"].lower()
