"""Tests for provider detection and model utilities."""

from unittest.mock import MagicMock, patch

import pytest

from quorum.providers import (
    ModelInfo,
    format_display_name,
    get_provider_for_model,
    list_all_models_sync,
)


class TestFormatDisplayName:
    """Tests for format_display_name function."""

    def test_removes_date_suffix_dashes(self):
        """Test removing YYYY-MM-DD date suffix."""
        result = format_display_name("gpt-4o-2024-08-06")
        assert "2024-08-06" not in result

    def test_removes_date_suffix_compact(self):
        """Test removing YYYYMMDD date suffix."""
        result = format_display_name("claude-opus-4-5-20251101")
        assert "20251101" not in result

    def test_converts_version_dashes(self):
        """Test converting 4-5 to 4.5."""
        result = format_display_name("claude-opus-4-5")
        assert "4.5" in result

    def test_capitalizes_parts(self):
        """Test that parts are capitalized."""
        result = format_display_name("claude-sonnet")
        assert result == "Claude Sonnet"

    def test_uppercases_known_acronyms(self):
        """Test that GPT is uppercased."""
        result = format_display_name("gpt-4o-mini")
        assert "GPT" in result

    def test_preserves_o_series(self):
        """Test that o3, o1, etc are preserved."""
        result = format_display_name("o3-mini")
        assert result == "o3 Mini"

    def test_preserves_version_numbers(self):
        """Test that version numbers are preserved."""
        result = format_display_name("gpt-4.1")
        assert "4.1" in result

    def test_complex_model_name(self):
        """Test formatting complex model name."""
        result = format_display_name("grok-4-1-fast-reasoning")
        # Should have version converted
        assert "4.1" in result or "4" in result

    def test_gemini_model(self):
        """Test Gemini model formatting."""
        result = format_display_name("gemini-2.5-pro")
        assert "Gemini" in result
        assert "Pro" in result


class TestGetProviderForModel:
    """Tests for config-based provider lookup."""

    @patch("quorum.providers.get_settings")
    def test_openai_models_from_config(self, mock_get_settings):
        """Models in OPENAI_MODELS should return 'openai'."""
        mock_settings = MagicMock()
        mock_settings.get_models.side_effect = lambda p: {
            "openai": ["gpt-4.1", "gpt-4.1-mini", "o3", "o3-mini"],
            "anthropic": [],
            "google": [],
            "xai": []
        }.get(p, [])
        mock_get_settings.return_value = mock_settings

        assert get_provider_for_model("gpt-4.1") == "openai"
        assert get_provider_for_model("gpt-4.1-mini") == "openai"
        assert get_provider_for_model("o3") == "openai"
        assert get_provider_for_model("o3-mini") == "openai"

    @patch("quorum.providers.get_settings")
    def test_anthropic_models_from_config(self, mock_get_settings):
        """Models in ANTHROPIC_MODELS should return 'anthropic'."""
        mock_settings = MagicMock()
        mock_settings.get_models.side_effect = lambda p: {
            "openai": [],
            "anthropic": ["claude-opus-4-5", "claude-sonnet-4-5"],
            "google": [],
            "xai": []
        }.get(p, [])
        mock_get_settings.return_value = mock_settings

        assert get_provider_for_model("claude-opus-4-5") == "anthropic"
        assert get_provider_for_model("claude-sonnet-4-5") == "anthropic"

    @patch("quorum.providers.get_settings")
    def test_google_models_from_config(self, mock_get_settings):
        """Models in GOOGLE_MODELS should return 'google'."""
        mock_settings = MagicMock()
        mock_settings.get_models.side_effect = lambda p: {
            "openai": [],
            "anthropic": [],
            "google": ["gemini-2.5-pro", "gemini-2.5-flash"],
            "xai": []
        }.get(p, [])
        mock_get_settings.return_value = mock_settings

        assert get_provider_for_model("gemini-2.5-pro") == "google"
        assert get_provider_for_model("gemini-2.5-flash") == "google"

    @patch("quorum.providers.get_settings")
    def test_xai_models_from_config(self, mock_get_settings):
        """Models in XAI_MODELS should return 'xai'."""
        mock_settings = MagicMock()
        mock_settings.get_models.side_effect = lambda p: {
            "openai": [],
            "anthropic": [],
            "google": [],
            "xai": ["grok-3", "grok-3-mini"]
        }.get(p, [])
        mock_get_settings.return_value = mock_settings

        assert get_provider_for_model("grok-3") == "xai"
        assert get_provider_for_model("grok-3-mini") == "xai"

    def test_ollama_prefix_routing(self):
        """Models with 'ollama:' prefix should return 'ollama'."""
        # Ollama uses prefix-based routing, no config lookup needed
        assert get_provider_for_model("ollama:llama3") == "ollama"
        assert get_provider_for_model("ollama:mistral") == "ollama"
        assert get_provider_for_model("ollama:codellama:7b") == "ollama"

    @patch("quorum.providers.get_settings")
    def test_unconfigured_model_returns_none(self, mock_get_settings):
        """Models not in any .env list should return None."""
        mock_settings = MagicMock()
        mock_settings.get_models.return_value = []  # No models configured
        mock_get_settings.return_value = mock_settings

        assert get_provider_for_model("fake-model-99") is None
        assert get_provider_for_model("unknown") is None

    @patch("quorum.providers.get_settings")
    def test_first_match_wins(self, mock_get_settings):
        """If model in multiple lists, first provider wins."""
        mock_settings = MagicMock()
        mock_settings.get_models.side_effect = lambda p: {
            "openai": ["duplicate-model"],
            "anthropic": ["duplicate-model"],  # Also in this list
            "google": [],
            "xai": []
        }.get(p, [])
        mock_get_settings.return_value = mock_settings

        # Should return openai (checked first)
        assert get_provider_for_model("duplicate-model") == "openai"


class TestModelInfo:
    """Tests for ModelInfo dataclass."""

    def test_create_model_info(self):
        """Test creating ModelInfo."""
        info = ModelInfo(id="gpt-4o", provider="openai")
        assert info.id == "gpt-4o"
        assert info.provider == "openai"
        assert info.display_name is None

    def test_create_model_info_with_display_name(self):
        """Test creating ModelInfo with display name."""
        info = ModelInfo(id="gpt-4o", provider="openai", display_name="GPT 4o")
        assert info.display_name == "GPT 4o"


class TestListAllModelsSync:
    """Tests for list_all_models_sync function."""

    def test_returns_dict_with_all_providers(self):
        """Test that all config-based providers are returned.

        Note: Ollama is NOT included here because it uses auto-discovery
        instead of config-based model lists.
        """
        with patch("quorum.providers.get_settings") as mock_settings:
            mock = MagicMock()
            mock.get_models_with_display_names.return_value = []
            mock_settings.return_value = mock

            result = list_all_models_sync()

            assert "openai" in result
            assert "anthropic" in result
            assert "google" in result
            assert "xai" in result
            # Ollama uses auto-discovery, not config-based listing
            assert "ollama" not in result

    def test_returns_model_info_objects(self):
        """Test that ModelInfo objects are returned."""
        with patch("quorum.providers.get_settings") as mock_settings:
            mock = MagicMock()
            mock.get_models_with_display_names.side_effect = lambda p: (
                [("gpt-4o", "GPT 4o")] if p == "openai" else []
            )
            mock_settings.return_value = mock

            result = list_all_models_sync()

            assert len(result["openai"]) == 1
            assert isinstance(result["openai"][0], ModelInfo)
            assert result["openai"][0].id == "gpt-4o"
            assert result["openai"][0].display_name == "GPT 4o"


class TestDiscoverOllamaModels:
    """Tests for discover_ollama_models function."""

    @pytest.mark.asyncio
    async def test_returns_empty_when_ollama_not_configured(self):
        """Test that empty list is returned when Ollama is not configured."""
        from quorum.providers import discover_ollama_models

        with patch("quorum.providers.get_settings") as mock_settings:
            mock = MagicMock()
            mock.has_ollama = False
            mock_settings.return_value = mock

            result = await discover_ollama_models()

            assert result == []

    @pytest.mark.asyncio
    async def test_returns_models_from_ollama_api(self):
        """Test that models are returned from Ollama API."""

        from quorum.providers import discover_ollama_models

        with patch("quorum.providers.get_settings") as mock_settings:
            mock = MagicMock()
            mock.has_ollama = True
            mock.ollama_base_url = "http://localhost:11434"
            mock.ollama_api_key = None
            mock_settings.return_value = mock

            # Mock httpx response
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = {
                "models": [
                    {"name": "llama3"},
                    {"name": "mistral:7b"},
                ]
            }

            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

                result = await discover_ollama_models()

                assert len(result) == 2
                assert result[0][0] == "ollama:llama3"
                assert result[1][0] == "ollama:mistral:7b"

    @pytest.mark.asyncio
    async def test_returns_empty_on_connection_error(self):
        """Test that empty list is returned on connection error."""
        import httpx

        from quorum.providers import discover_ollama_models

        with patch("quorum.providers.get_settings") as mock_settings:
            mock = MagicMock()
            mock.has_ollama = True
            mock.ollama_base_url = "http://localhost:11434"
            mock.ollama_api_key = None
            mock_settings.return_value = mock

            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.get.side_effect = (
                    httpx.ConnectError("Connection refused")
                )

                result = await discover_ollama_models()

                assert result == []
