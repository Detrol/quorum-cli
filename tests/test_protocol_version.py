"""Tests for protocol versioning.

Tests protocol version checking and compatibility warnings.
"""

import json

import pytest

from quorum.ipc import PROTOCOL_VERSION, IPCHandler


@pytest.fixture
def ipc_handler():
    """Create an IPCHandler instance for testing."""
    return IPCHandler()


class TestProtocolVersionConstant:
    """Tests for protocol version constant."""

    def test_protocol_version_format(self):
        """Test that protocol version follows semantic versioning."""
        parts = PROTOCOL_VERSION.split(".")
        assert len(parts) == 3, "Protocol version should have 3 parts (MAJOR.MINOR.PATCH)"
        for part in parts:
            assert part.isdigit(), f"Version part '{part}' should be numeric"

    def test_protocol_version_is_exported(self):
        """Test that PROTOCOL_VERSION is accessible."""
        from quorum.ipc import PROTOCOL_VERSION
        assert PROTOCOL_VERSION is not None
        assert isinstance(PROTOCOL_VERSION, str)


class TestInitializeWithVersion:
    """Tests for initialize handler with protocol version."""

    @pytest.mark.asyncio
    async def test_initialize_returns_protocol_version(self, ipc_handler, capsys):
        """Test that initialize returns protocol_version."""
        request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "id": 1,
            "params": {}
        }
        await ipc_handler.handle_request(request)

        captured = capsys.readouterr()
        response = json.loads(captured.out.strip())

        assert "result" in response
        assert "protocol_version" in response["result"]
        assert response["result"]["protocol_version"] == PROTOCOL_VERSION

    @pytest.mark.asyncio
    async def test_initialize_with_matching_version(self, ipc_handler, capsys):
        """Test initialize with matching frontend version."""
        request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "id": 1,
            "params": {"protocol_version": PROTOCOL_VERSION}
        }
        await ipc_handler.handle_request(request)

        captured = capsys.readouterr()
        response = json.loads(captured.out.strip())

        assert "result" in response
        assert "version_warning" not in response["result"]

    @pytest.mark.asyncio
    async def test_initialize_with_older_frontend(self, ipc_handler, capsys):
        """Test initialize with older frontend version."""
        # Parse current version and make frontend one minor version older
        parts = [int(x) for x in PROTOCOL_VERSION.split(".")]
        older_version = f"{parts[0]}.{max(0, parts[1] - 1)}.0"

        request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "id": 1,
            "params": {"protocol_version": older_version}
        }
        await ipc_handler.handle_request(request)

        captured = capsys.readouterr()
        response = json.loads(captured.out.strip())

        # Should have a warning if versions differ
        if older_version != PROTOCOL_VERSION:
            assert "version_warning" in response["result"]

    @pytest.mark.asyncio
    async def test_initialize_with_newer_frontend(self, ipc_handler, capsys):
        """Test initialize with newer frontend version."""
        parts = [int(x) for x in PROTOCOL_VERSION.split(".")]
        newer_version = f"{parts[0]}.{parts[1] + 1}.0"

        request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "id": 1,
            "params": {"protocol_version": newer_version}
        }
        await ipc_handler.handle_request(request)

        captured = capsys.readouterr()
        response = json.loads(captured.out.strip())

        assert "version_warning" in response["result"]
        assert "newer protocol" in response["result"]["version_warning"].lower()

    @pytest.mark.asyncio
    async def test_initialize_with_major_version_mismatch(self, ipc_handler, capsys):
        """Test initialize with major version mismatch."""
        parts = [int(x) for x in PROTOCOL_VERSION.split(".")]
        different_major = f"{parts[0] + 1}.0.0"

        request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "id": 1,
            "params": {"protocol_version": different_major}
        }
        await ipc_handler.handle_request(request)

        captured = capsys.readouterr()
        response = json.loads(captured.out.strip())

        assert "version_warning" in response["result"]
        assert "major version" in response["result"]["version_warning"].lower()


class TestVersionCompatibilityChecker:
    """Tests for _check_protocol_compatibility method."""

    def test_matching_versions(self, ipc_handler):
        """Test that matching versions return no warning."""
        result = ipc_handler._check_protocol_compatibility(PROTOCOL_VERSION)
        assert result is None

    def test_major_version_mismatch(self, ipc_handler):
        """Test major version mismatch detection."""
        parts = [int(x) for x in PROTOCOL_VERSION.split(".")]
        different = f"{parts[0] + 1}.0.0"

        result = ipc_handler._check_protocol_compatibility(different)
        assert result is not None
        assert "major version" in result.lower()

    def test_minor_version_newer_backend(self, ipc_handler):
        """Test when backend has newer minor version."""
        parts = [int(x) for x in PROTOCOL_VERSION.split(".")]
        older = f"{parts[0]}.{max(0, parts[1] - 1)}.0"

        if older != PROTOCOL_VERSION:
            result = ipc_handler._check_protocol_compatibility(older)
            assert result is None or "newer protocol" in result.lower()

    def test_minor_version_newer_frontend(self, ipc_handler):
        """Test when frontend has newer minor version."""
        parts = [int(x) for x in PROTOCOL_VERSION.split(".")]
        newer = f"{parts[0]}.{parts[1] + 1}.0"

        result = ipc_handler._check_protocol_compatibility(newer)
        assert result is not None
        assert "newer protocol" in result.lower() or "updating" in result.lower()

    def test_invalid_version_format(self, ipc_handler):
        """Test handling of invalid version format."""
        result = ipc_handler._check_protocol_compatibility("invalid")
        assert result is not None
        assert "invalid" in result.lower()

    def test_empty_version(self, ipc_handler):
        """Test handling of empty version string."""
        result = ipc_handler._check_protocol_compatibility("")
        assert result is not None
