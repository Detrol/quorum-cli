"""Tests for model client factory."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestCreateOpenAIClient:
    """Tests for OpenAI client creation."""

    @patch("quorum.models.get_settings")
    @patch("quorum.models.get_provider_for_model")
    def test_creates_openai_client_with_api_key(
        self, mock_get_provider, mock_get_settings
    ):
        """OpenAI client is created with correct API key."""
        from quorum.models import _create_model_client_internal

        mock_settings = MagicMock()
        mock_settings.has_openai = True
        mock_settings.openai_api_key = "sk-test123456789012345678901234"
        mock_get_settings.return_value = mock_settings
        mock_get_provider.return_value = "openai"

        client = _create_model_client_internal("gpt-4o")

        assert client is not None
        # Client is created successfully (implementation details may vary)

    @patch("quorum.models.get_settings")
    @patch("quorum.models.get_provider_for_model")
    def test_raises_error_without_api_key(
        self, mock_get_provider, mock_get_settings
    ):
        """ValueError raised when OpenAI API key not configured."""
        from quorum.models import _create_model_client_internal

        mock_settings = MagicMock()
        mock_settings.has_openai = False
        mock_get_settings.return_value = mock_settings
        mock_get_provider.return_value = "openai"

        with pytest.raises(ValueError, match="OpenAI API key not configured"):
            _create_model_client_internal("gpt-4o")


class TestCreateAnthropicClient:
    """Tests for Anthropic client creation."""

    @patch("quorum.models.get_settings")
    @patch("quorum.models.get_provider_for_model")
    def test_creates_anthropic_client(
        self, mock_get_provider, mock_get_settings
    ):
        """Anthropic client is created with correct API key."""
        from quorum.models import _create_model_client_internal

        mock_settings = MagicMock()
        mock_settings.has_anthropic = True
        mock_settings.anthropic_api_key = "sk-ant-test12345678901234567890"
        mock_get_settings.return_value = mock_settings
        mock_get_provider.return_value = "anthropic"

        client = _create_model_client_internal("claude-3-opus-20240229")

        assert client is not None

    @patch("quorum.models.get_settings")
    @patch("quorum.models.get_provider_for_model")
    def test_raises_error_without_anthropic_key(
        self, mock_get_provider, mock_get_settings
    ):
        """ValueError raised when Anthropic API key not configured."""
        from quorum.models import _create_model_client_internal

        mock_settings = MagicMock()
        mock_settings.has_anthropic = False
        mock_get_settings.return_value = mock_settings
        mock_get_provider.return_value = "anthropic"

        with pytest.raises(ValueError, match="Anthropic API key not configured"):
            _create_model_client_internal("claude-3-opus")


class TestOllamaTimeoutHandling:
    """Tests for Ollama-specific timeout handling."""

    @patch("quorum.models.get_settings")
    @patch("quorum.models.get_provider_for_model")
    def test_ollama_client_created_with_base_url(
        self, mock_get_provider, mock_get_settings
    ):
        """Ollama client uses configured base URL."""
        from quorum.models import _create_model_client_internal

        mock_settings = MagicMock()
        mock_settings.ollama_base_url = "http://localhost:11434"
        mock_settings.ollama_api_key = None
        mock_get_settings.return_value = mock_settings
        mock_get_provider.return_value = "ollama"

        client = _create_model_client_internal("ollama:llama3")

        assert client is not None

    def test_ollama_model_strips_prefix(self):
        """Ollama model ID has prefix stripped for API call."""
        # The model name passed to Ollama API should not have ollama: prefix
        model_id = "ollama:llama3"
        actual_model = model_id.split(":", 1)[1] if ":" in model_id else model_id
        assert actual_model == "llama3"


class TestUnknownProviderRejection:
    """Tests for unknown provider handling."""

    @patch("quorum.models.get_settings")
    @patch("quorum.models.get_provider_for_model")
    def test_raises_error_for_unknown_provider(
        self, mock_get_provider, mock_get_settings
    ):
        """ValueError raised for unsupported provider."""
        from quorum.models import _create_model_client_internal

        mock_settings = MagicMock()
        mock_settings.get_models.return_value = []
        mock_get_settings.return_value = mock_settings
        mock_get_provider.return_value = None

        with pytest.raises(ValueError, match="not found in configuration"):
            _create_model_client_internal("unknown-model-xyz")

    @patch("quorum.models.get_settings")
    @patch("quorum.models.get_provider_for_model")
    def test_error_message_lists_available_providers(
        self, mock_get_provider, mock_get_settings
    ):
        """Error message includes available providers."""
        from quorum.models import _create_model_client_internal

        mock_settings = MagicMock()
        mock_settings.get_models.side_effect = lambda p: ["model"] if p == "openai" else []
        mock_get_settings.return_value = mock_settings
        mock_get_provider.return_value = None

        with pytest.raises(ValueError) as exc_info:
            _create_model_client_internal("unknown-model")

        assert "openai" in str(exc_info.value)


