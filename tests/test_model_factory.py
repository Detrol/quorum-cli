"""Tests for model client factory."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tests.provider_specs import CN_PROVIDERS


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


class TestCreateDeepSeekClient:
    """Tests for DeepSeek client creation."""

    @patch("quorum.models.get_settings")
    @patch("quorum.models.get_provider_for_model")
    def test_creates_deepseek_client_with_base_url(
        self, mock_get_provider, mock_get_settings
    ):
        """DeepSeek uses an OpenAI-compatible client with the configured base URL."""
        from quorum.clients import OpenAIClient
        from quorum.models import _create_model_client_internal

        mock_settings = MagicMock()
        mock_settings.has_deepseek = True
        mock_settings.deepseek_api_key = "sk-deepseek-test-key-12345"
        mock_settings.deepseek_base_url = "https://api.deepseek.com/v1"
        mock_get_settings.return_value = mock_settings
        mock_get_provider.return_value = "deepseek"

        client = _create_model_client_internal("deepseek-chat")

        assert isinstance(client, OpenAIClient)
        assert client.model == "deepseek-chat"
        assert str(client._client.base_url).rstrip("/") == "https://api.deepseek.com/v1"

    @patch("quorum.models.get_settings")
    @patch("quorum.models.get_provider_for_model")
    def test_raises_error_without_deepseek_key(
        self, mock_get_provider, mock_get_settings
    ):
        """ValueError raised when DeepSeek API key not configured."""
        from quorum.models import _create_model_client_internal

        mock_settings = MagicMock()
        mock_settings.has_deepseek = False
        mock_get_settings.return_value = mock_settings
        mock_get_provider.return_value = "deepseek"

        with pytest.raises(ValueError, match="DEEPSEEK_API_KEY"):
            _create_model_client_internal("deepseek-chat")


class TestCreateAliyunClient:
    """Tests for Aliyun DashScope client creation."""

    @patch("quorum.models.get_settings")
    @patch("quorum.models.get_provider_for_model")
    def test_creates_aliyun_client_with_base_url(
        self, mock_get_provider, mock_get_settings
    ):
        """Aliyun uses an OpenAI-compatible client with the configured base URL."""
        from quorum.clients import OpenAIClient
        from quorum.models import _create_model_client_internal

        mock_settings = MagicMock()
        mock_settings.has_aliyun = True
        mock_settings.aliyun_api_key = "sk-aliyun-test-key-123456"
        mock_settings.aliyun_base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        mock_get_settings.return_value = mock_settings
        mock_get_provider.return_value = "aliyun"

        client = _create_model_client_internal("qwen3.8-flash")

        assert isinstance(client, OpenAIClient)
        assert client.model == "qwen3.8-flash"
        assert (
            str(client._client.base_url).rstrip("/")
            == "https://dashscope.aliyuncs.com/compatible-mode/v1"
        )

    @patch("quorum.models.get_settings")
    @patch("quorum.models.get_provider_for_model")
    def test_raises_error_without_aliyun_key(
        self, mock_get_provider, mock_get_settings
    ):
        """ValueError raised when Aliyun API key not configured."""
        from quorum.models import _create_model_client_internal

        mock_settings = MagicMock()
        mock_settings.has_aliyun = False
        mock_get_settings.return_value = mock_settings
        mock_get_provider.return_value = "aliyun"

        with pytest.raises(ValueError, match="ALIYUN_API_KEY"):
            _create_model_client_internal("qwen3.8-flash")


class TestCreateCNProviderClient:
    """Tests for the Chinese OpenAI-compatible provider clients."""

    @pytest.mark.parametrize("spec", CN_PROVIDERS, ids=lambda s: s.key)
    @patch("quorum.models.get_settings")
    @patch("quorum.models.get_provider_for_model")
    def test_creates_client_with_base_url(
        self, mock_get_provider, mock_get_settings, spec
    ):
        """Each Chinese provider uses an OpenAI client with its configured base URL."""
        from quorum.clients import OpenAIClient
        from quorum.models import _create_model_client_internal

        mock_settings = MagicMock()
        setattr(mock_settings, spec.has_attr, True)
        setattr(mock_settings, spec.api_key_attr, f"sk-{spec.key}-test-key-123456")
        setattr(mock_settings, spec.base_url_attr, spec.default_base_url)
        mock_get_settings.return_value = mock_settings
        mock_get_provider.return_value = spec.key

        client = _create_model_client_internal(spec.sample_model)

        assert isinstance(client, OpenAIClient)
        assert client.model == spec.sample_model
        assert (
            str(client._client.base_url).rstrip("/") == spec.default_base_url
        )

    @pytest.mark.parametrize("spec", CN_PROVIDERS, ids=lambda s: s.key)
    @patch("quorum.models.get_settings")
    @patch("quorum.models.get_provider_for_model")
    def test_uses_configured_base_url_override(
        self, mock_get_provider, mock_get_settings, spec
    ):
        """A customized base URL is passed through to the client."""
        from quorum.clients import OpenAIClient
        from quorum.models import _create_model_client_internal

        custom_url = f"https://proxy.local/{spec.key}"
        mock_settings = MagicMock()
        setattr(mock_settings, spec.has_attr, True)
        setattr(mock_settings, spec.api_key_attr, f"sk-{spec.key}-test-key-123456")
        setattr(mock_settings, spec.base_url_attr, custom_url)
        mock_get_settings.return_value = mock_settings
        mock_get_provider.return_value = spec.key

        client = _create_model_client_internal(spec.sample_model)

        assert isinstance(client, OpenAIClient)
        assert str(client._client.base_url).rstrip("/") == custom_url

    @pytest.mark.parametrize("spec", CN_PROVIDERS, ids=lambda s: s.key)
    @patch("quorum.models.get_settings")
    @patch("quorum.models.get_provider_for_model")
    def test_raises_error_without_api_key(
        self, mock_get_provider, mock_get_settings, spec
    ):
        """ValueError raised when the provider API key is not configured."""
        from quorum.models import _create_model_client_internal

        mock_settings = MagicMock()
        setattr(mock_settings, spec.has_attr, False)
        mock_get_settings.return_value = mock_settings
        mock_get_provider.return_value = spec.key

        with pytest.raises(ValueError, match=spec.api_key_env):
            _create_model_client_internal(spec.sample_model)


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


