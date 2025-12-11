"""Tests for configuration module."""

import json

import pytest

import quorum.config
from quorum.config import (
    Settings,
    add_to_input_history,
    get_input_history,
    get_user_settings,
    get_validated_models_cache,
    save_user_settings,
    save_validated_model,
)


@pytest.fixture(autouse=True)
def enable_test_mode():
    """Enable test mode to bypass home directory validation in _write_secure_file."""
    original = quorum.config._TEST_MODE
    quorum.config._TEST_MODE = True
    yield
    quorum.config._TEST_MODE = original


class TestValidatedModelsCache:
    """Tests for validated models cache functions."""

    def test_get_validated_models_cache_empty(self, tmp_path, monkeypatch):
        """Test getting cache when file doesn't exist."""
        monkeypatch.setattr("quorum.config.VALIDATED_MODELS_CACHE", tmp_path / "nonexistent.json")
        result = get_validated_models_cache()
        assert result == set()

    def test_get_validated_models_cache_with_data(self, tmp_path, monkeypatch):
        """Test getting cache with existing data."""
        cache_file = tmp_path / "validated.json"
        cache_file.write_text(json.dumps({"models": ["model-a", "model-b"]}))
        monkeypatch.setattr("quorum.config.VALIDATED_MODELS_CACHE", cache_file)

        result = get_validated_models_cache()
        assert result == {"model-a", "model-b"}

    def test_get_validated_models_cache_invalid_json(self, tmp_path, monkeypatch):
        """Test handling of invalid JSON."""
        cache_file = tmp_path / "validated.json"
        cache_file.write_text("not valid json")
        monkeypatch.setattr("quorum.config.VALIDATED_MODELS_CACHE", cache_file)

        result = get_validated_models_cache()
        assert result == set()

    def test_save_validated_model(self, tmp_path, monkeypatch):
        """Test saving a validated model."""
        cache_dir = tmp_path / ".quorum"
        cache_file = cache_dir / "validated.json"
        monkeypatch.setattr("quorum.config.CACHE_DIR", cache_dir)
        monkeypatch.setattr("quorum.config.VALIDATED_MODELS_CACHE", cache_file)

        save_validated_model("new-model")

        assert cache_file.exists()
        data = json.loads(cache_file.read_text())
        assert "new-model" in data["models"]

    def test_cache_file_can_be_deleted(self, tmp_path, monkeypatch):
        """Test that cache file can be manually deleted for clearing."""
        cache_file = tmp_path / "validated.json"
        cache_file.write_text(json.dumps({"models": ["model-a"]}))
        monkeypatch.setattr("quorum.config.VALIDATED_MODELS_CACHE", cache_file)

        # Direct file deletion (what a clear function would do)
        cache_file.unlink()
        assert not cache_file.exists()
        # After deletion, cache returns empty
        assert get_validated_models_cache() == set()


class TestUserSettings:
    """Tests for user settings cache functions."""

    def test_get_user_settings_empty(self, tmp_path, monkeypatch):
        """Test getting settings when file doesn't exist."""
        monkeypatch.setattr("quorum.config.USER_SETTINGS_CACHE", tmp_path / "nonexistent.json")
        result = get_user_settings()
        assert result == {}

    def test_get_user_settings_with_data(self, tmp_path, monkeypatch):
        """Test getting settings with existing data."""
        cache_file = tmp_path / "settings.json"
        cache_file.write_text(json.dumps({"theme": "dark", "models": ["a", "b"]}))
        monkeypatch.setattr("quorum.config.USER_SETTINGS_CACHE", cache_file)

        result = get_user_settings()
        assert result == {"theme": "dark", "models": ["a", "b"]}

    def test_save_user_settings_merge(self, tmp_path, monkeypatch):
        """Test that settings are merged with existing."""
        cache_dir = tmp_path / ".quorum"
        cache_file = cache_dir / "settings.json"
        cache_dir.mkdir()
        # Start with one valid setting
        cache_file.write_text(json.dumps({"discussion_method": "standard"}))
        monkeypatch.setattr("quorum.config.CACHE_DIR", cache_dir)
        monkeypatch.setattr("quorum.config.USER_SETTINGS_CACHE", cache_file)

        # Add another valid setting
        save_user_settings({"max_turns": 5})

        data = json.loads(cache_file.read_text())
        assert data == {"discussion_method": "standard", "max_turns": 5}


class TestInputHistory:
    """Tests for input history functions."""

    def test_get_input_history_empty(self, tmp_path, monkeypatch):
        """Test getting history when file doesn't exist."""
        monkeypatch.setattr("quorum.config.INPUT_HISTORY_CACHE", tmp_path / "nonexistent.json")
        result = get_input_history()
        assert result == []

    def test_get_input_history_with_data(self, tmp_path, monkeypatch):
        """Test getting history with existing data."""
        cache_file = tmp_path / "history.json"
        cache_file.write_text(json.dumps({"history": ["query1", "query2"]}))
        monkeypatch.setattr("quorum.config.INPUT_HISTORY_CACHE", cache_file)

        result = get_input_history()
        assert result == ["query1", "query2"]

    def test_add_to_input_history(self, tmp_path, monkeypatch):
        """Test adding to history."""
        cache_dir = tmp_path / ".quorum"
        cache_file = cache_dir / "history.json"
        monkeypatch.setattr("quorum.config.CACHE_DIR", cache_dir)
        monkeypatch.setattr("quorum.config.INPUT_HISTORY_CACHE", cache_file)

        add_to_input_history("new query")

        data = json.loads(cache_file.read_text())
        assert "new query" in data["history"]

    def test_add_to_input_history_deduplicates(self, tmp_path, monkeypatch):
        """Test that duplicate entries are moved to end."""
        cache_dir = tmp_path / ".quorum"
        cache_file = cache_dir / "history.json"
        cache_dir.mkdir()
        cache_file.write_text(json.dumps({"history": ["a", "b", "c"]}))
        monkeypatch.setattr("quorum.config.CACHE_DIR", cache_dir)
        monkeypatch.setattr("quorum.config.INPUT_HISTORY_CACHE", cache_file)

        add_to_input_history("a")  # "a" already exists

        data = json.loads(cache_file.read_text())
        assert data["history"] == ["b", "c", "a"]  # "a" moved to end

    def test_add_to_input_history_limits_size(self, tmp_path, monkeypatch):
        """Test that history is limited to max_items."""
        cache_dir = tmp_path / ".quorum"
        cache_file = cache_dir / "history.json"
        cache_dir.mkdir()
        cache_file.write_text(json.dumps({"history": list(range(10))}))
        monkeypatch.setattr("quorum.config.CACHE_DIR", cache_dir)
        monkeypatch.setattr("quorum.config.INPUT_HISTORY_CACHE", cache_file)

        add_to_input_history("new", max_items=5)

        data = json.loads(cache_file.read_text())
        assert len(data["history"]) == 5
        assert data["history"][-1] == "new"


class TestSettings:
    """Tests for Settings class.

    Note: These tests use monkeypatch to set/clear environment variables.
    pydantic-settings reads from environment variables using the Field alias.
    """

    @pytest.fixture(autouse=True)
    def clear_env(self, monkeypatch):
        """Clear all API key environment variables for isolated tests."""
        env_vars = [
            "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "XAI_API_KEY",
            "OPENAI_MODELS", "ANTHROPIC_MODELS", "GOOGLE_MODELS", "XAI_MODELS",
            "QUORUM_METHOD", "QUORUM_SYNTHESIZER", "QUORUM_ROUNDS_PER_AGENT",
            "QUORUM_DEFAULT_LANGUAGE",
        ]
        for var in env_vars:
            monkeypatch.delenv(var, raising=False)

    def test_get_models_empty(self):
        """Test getting models when none configured."""
        settings = Settings(_env_file=None)
        result = settings.get_models("openai")
        assert result == []

    def test_get_models_parses_comma_separated(self, monkeypatch):
        """Test parsing comma-separated model list."""
        monkeypatch.setenv("OPENAI_MODELS", "gpt-4o, gpt-4o-mini, o3")
        settings = Settings(_env_file=None)
        result = settings.get_models("openai")
        assert result == ["gpt-4o", "gpt-4o-mini", "o3"]

    def test_get_models_handles_display_name_format(self, monkeypatch):
        """Test that display name format is stripped."""
        monkeypatch.setenv("OPENAI_MODELS", "gpt-4o|GPT 4o, gpt-4o-mini|Mini")
        settings = Settings(_env_file=None)
        result = settings.get_models("openai")
        assert result == ["gpt-4o", "gpt-4o-mini"]

    def test_get_models_with_display_names(self, monkeypatch):
        """Test getting models with display names."""
        monkeypatch.setenv("OPENAI_MODELS", "gpt-4o|Custom Name")
        settings = Settings(_env_file=None)
        result = settings.get_models_with_display_names("openai")
        assert result == [("gpt-4o", "Custom Name")]

    def test_available_providers_none(self):
        """Test available providers when no API keys set.

        Note: Ollama is always available by default since it uses a local
        server with a default URL and doesn't require an API key.
        """
        settings = Settings(_env_file=None)
        # Ollama is always available (local, no API key required)
        assert settings.available_providers == ["ollama"]

    def test_available_providers_some(self, monkeypatch):
        """Test available providers with some keys."""
        # API keys must be at least 20 chars for validation
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-openai-key-12345")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key-12345678")
        settings = Settings(_env_file=None)
        assert "openai" in settings.available_providers
        assert "anthropic" in settings.available_providers
        assert "google" not in settings.available_providers

    def test_has_provider_properties(self, monkeypatch):
        """Test has_* properties."""
        # API key must be at least 20 chars for validation
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-openai-key-12345")
        settings = Settings(_env_file=None)
        assert settings.has_openai is True
        assert settings.has_anthropic is False
        assert settings.has_google is False
        assert settings.has_xai is False

    def test_synthesizer_mode_default(self):
        """Test default synthesizer mode."""
        settings = Settings(_env_file=None)
        assert settings.synthesizer_mode == "first"

    def test_rounds_per_agent_default(self):
        """Test default rounds per agent."""
        settings = Settings(_env_file=None)
        assert settings.rounds_per_agent == 2
