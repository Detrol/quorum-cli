"""Tests for client connection pooling.

Tests the ClientPool class for efficient connection reuse.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from quorum.models import MAX_POOL_SIZE, ClientPool


@pytest.fixture
def pool():
    """Create a fresh ClientPool for testing."""
    # Reset singleton for isolated tests
    ClientPool._instance = None
    ClientPool._lock = None
    return ClientPool.get_instance()


@pytest.fixture
def mock_create_client():
    """Mock the client creation function."""
    with patch("quorum.models._create_model_client_internal") as mock:
        # Create mock clients with async close
        def create_mock_client(model_id):
            client = MagicMock()
            client.close = AsyncMock()
            client.model_id = model_id  # Track which model this is for
            return client
        mock.side_effect = create_mock_client
        yield mock


class TestClientPoolBasic:
    """Basic pool functionality tests."""

    @pytest.mark.asyncio
    async def test_get_client_creates_new(self, pool, mock_create_client):
        """Test that get_client creates a new client if not in pool."""
        client = await pool.get_client("gpt-4o")

        assert client is not None
        mock_create_client.assert_called_once_with("gpt-4o")

    @pytest.mark.asyncio
    async def test_get_client_reuses_existing(self, pool, mock_create_client):
        """Test that get_client reuses existing client."""
        client1 = await pool.get_client("gpt-4o")
        client2 = await pool.get_client("gpt-4o")

        assert client1 is client2
        mock_create_client.assert_called_once()

    @pytest.mark.asyncio
    async def test_different_models_get_different_clients(self, pool, mock_create_client):
        """Test that different models get different clients."""
        client1 = await pool.get_client("gpt-4o")
        client2 = await pool.get_client("claude-sonnet")

        assert client1 is not client2
        assert mock_create_client.call_count == 2


class TestClientPoolEviction:
    """Tests for LRU eviction behavior."""

    @pytest.mark.asyncio
    async def test_evicts_oldest_when_full(self, pool, mock_create_client):
        """Test that oldest client is evicted when pool is full."""
        # Fill the pool
        for i in range(MAX_POOL_SIZE):
            await pool.get_client(f"model-{i}")

        # Add one more - should evict model-0
        await pool.get_client("new-model")

        # model-0 should be evicted (removed from pool, not closed)
        assert mock_create_client.call_count == MAX_POOL_SIZE + 1

        # Get model-0 again - should create new one
        await pool.get_client("model-0")
        assert mock_create_client.call_count == MAX_POOL_SIZE + 2

    @pytest.mark.asyncio
    async def test_lru_access_updates_order(self, pool, mock_create_client):
        """Test that accessing a client moves it to end of eviction order."""
        # Fill pool partially
        await pool.get_client("model-a")
        await pool.get_client("model-b")
        await pool.get_client("model-c")

        # Access model-a again (should move to end)
        await pool.get_client("model-a")

        # Check access order (OrderedDict maintains insertion/access order)
        assert list(pool._clients.keys()) == ["model-b", "model-c", "model-a"]


class TestClientPoolCleanup:
    """Tests for pool cleanup operations."""

    @pytest.mark.asyncio
    async def test_close_all_clears_pool_without_closing_clients(self, pool, mock_create_client):
        """Test that close_all clears pool but doesn't close individual clients.

        Note: We don't close individual clients because OpenAI-compatible clients
        share a common HTTP client. Closing one would break all others.
        The shared HTTP client is closed separately by close_pool().
        """
        client1 = await pool.get_client("gpt-4o")
        client2 = await pool.get_client("claude-sonnet")

        await pool.close_all()

        # close() should NOT be called (shared HTTP client issue)
        client1.close.assert_not_called()
        client2.close.assert_not_called()
        # But pool should be cleared
        assert len(pool._clients) == 0

    @pytest.mark.asyncio
    async def test_remove_client_removes_specific(self, pool, mock_create_client):
        """Test that remove_client removes only specific client from pool.

        Note: remove_client does NOT close the client (to avoid closing shared
        HTTP clients). The client is just removed and will be garbage collected.
        """
        await pool.get_client("gpt-4o")
        await pool.get_client("claude-sonnet")

        await pool.remove_client("gpt-4o")

        # Client removed from pool (not closed - see docstring)
        assert "gpt-4o" not in pool._clients
        assert "claude-sonnet" in pool._clients

    @pytest.mark.asyncio
    async def test_remove_nonexistent_client_is_safe(self, pool, mock_create_client):
        """Test that removing non-existent client doesn't error."""
        await pool.get_client("gpt-4o")

        # Should not raise
        await pool.remove_client("nonexistent")


class TestClientPoolConcurrency:
    """Tests for concurrent access to pool."""

    @pytest.mark.asyncio
    async def test_concurrent_access_same_model(self, pool, mock_create_client):
        """Test that concurrent access to same model creates only one client."""
        # Request same model concurrently
        clients = await asyncio.gather(
            pool.get_client("gpt-4o"),
            pool.get_client("gpt-4o"),
            pool.get_client("gpt-4o"),
        )

        # All should be the same client
        assert clients[0] is clients[1] is clients[2]
        mock_create_client.assert_called_once()

    @pytest.mark.asyncio
    async def test_concurrent_access_different_models(self, pool, mock_create_client):
        """Test that concurrent access to different models works."""
        clients = await asyncio.gather(
            pool.get_client("gpt-4o"),
            pool.get_client("claude-sonnet"),
            pool.get_client("gemini-pro"),
        )

        assert len(set(id(c) for c in clients)) == 3  # All different
        assert mock_create_client.call_count == 3


class TestPoolSingleton:
    """Tests for singleton pattern."""

    def test_get_instance_returns_same_instance(self):
        """Test that get_instance returns same pool."""
        # Reset for clean test
        ClientPool._instance = None

        pool1 = ClientPool.get_instance()
        pool2 = ClientPool.get_instance()

        assert pool1 is pool2


class TestPoolErrorHandling:
    """Tests for error handling in pool."""

    @pytest.mark.asyncio
    async def test_close_error_is_ignored(self, pool, mock_create_client):
        """Test that errors during close are handled gracefully."""
        client = await pool.get_client("gpt-4o")
        client.close.side_effect = RuntimeError("Close failed")

        # Should not raise
        await pool.close_all()

        # Pool should be empty
        assert len(pool._clients) == 0
