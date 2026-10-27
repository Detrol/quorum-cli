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
from tests.provider_specs import (
    ALL_COMPAT_PROVIDERS,
    CN_PROVIDERS,
    PROVIDER_ENV_VARS,
    QUORUM_ENV_VARS,
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
    def clear_env(self, monkeypatch, tmp_path):
        """Clear all API key environment variables for isolated tests.

        Also mocks _get_active_env_file to return a non-existent path,
        preventing tests from picking up real .env files.
        """
        env_vars = [
            *PROVIDER_ENV_VARS,
            *QUORUM_ENV_VARS,
        ]
        for var in env_vars:
            monkeypatch.delenv(var, raising=False)

        # Mock _get_active_env_file to return non-existent path
        # This prevents tests from loading real .env files
        monkeypatch.setattr(
            quorum.config,
            "_get_active_env_file",
            lambda: tmp_path / ".env.nonexistent",
        )

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

    def test_has_deepseek_aliyun_properties(self):
        """Test has_deepseek/has_aliyun are False when no keys set."""
        settings = Settings(_env_file=None)
        assert settings.has_deepseek is False
        assert settings.has_aliyun is False

    def test_has_deepseek_when_key_set(self, monkeypatch):
        """Test has_deepseek is True once DEEPSEEK_API_KEY is set."""
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-deepseek-test-key-12345")
        settings = Settings(_env_file=None)
        assert settings.has_deepseek is True
        assert settings.has_aliyun is False

    def test_has_aliyun_when_key_set(self, monkeypatch):
        """Test has_aliyun is True once ALIYUN_API_KEY is set."""
        monkeypatch.setenv("ALIYUN_API_KEY", "sk-aliyun-test-key-123456")
        settings = Settings(_env_file=None)
        assert settings.has_aliyun is True
        assert settings.has_deepseek is False

    def test_deepseek_aliyun_default_base_urls(self):
        """Test default base URLs for deepseek and aliyun."""
        settings = Settings(_env_file=None)
        assert settings.deepseek_base_url == "https://api.deepseek.com/v1"
        assert settings.aliyun_base_url == "https://dashscope.aliyuncs.com/compatible-mode/v1"

    def test_deepseek_aliyun_base_urls_overridable(self, monkeypatch):
        """Test DEEPSEEK_BASE_URL/ALIYUN_BASE_URL override the defaults."""
        monkeypatch.setenv("DEEPSEEK_BASE_URL", "https://proxy.local/deepseek")
        monkeypatch.setenv("ALIYUN_BASE_URL", "https://proxy.local/aliyun")
        settings = Settings(_env_file=None)
        assert settings.deepseek_base_url == "https://proxy.local/deepseek"
        assert settings.aliyun_base_url == "https://proxy.local/aliyun"

    def test_get_models_deepseek(self, monkeypatch):
        """Test parsing DEEPSEEK_MODELS."""
        monkeypatch.setenv("DEEPSEEK_MODELS", "deepseek-chat, deepseek-reasoner")
        settings = Settings(_env_file=None)
        assert settings.get_models("deepseek") == ["deepseek-chat", "deepseek-reasoner"]

    def test_get_models_aliyun(self, monkeypatch):
        """Test parsing ALIYUN_MODELS."""
        monkeypatch.setenv("ALIYUN_MODELS", "qwen3.8-flash")
        settings = Settings(_env_file=None)
        assert settings.get_models("aliyun") == ["qwen3.8-flash"]

    def test_available_providers_deepseek_aliyun(self, monkeypatch):
        """Test available_providers includes deepseek and aliyun when keys set."""
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-deepseek-test-key-12345")
        monkeypatch.setenv("ALIYUN_API_KEY", "sk-aliyun-test-key-123456")
        settings = Settings(_env_file=None)
        assert "deepseek" in settings.available_providers
        assert "aliyun" in settings.available_providers

    def test_available_providers_excludes_deepseek_aliyun(self):
        """Test deepseek/aliyun are absent from available_providers without keys."""
        settings = Settings(_env_file=None)
        assert "deepseek" not in settings.available_providers
        assert "aliyun" not in settings.available_providers

    def test_synthesizer_mode_default(self):
        """Test default synthesizer mode."""
        settings = Settings(_env_file=None)
        assert settings.synthesizer_mode == "first"

    def test_rounds_per_agent_default(self):
        """Test default rounds per agent."""
        settings = Settings(_env_file=None)
        assert settings.rounds_per_agent == 2

    @pytest.mark.parametrize("spec", CN_PROVIDERS, ids=lambda s: s.key)
    def test_cn_provider_default_base_url(self, spec):
        """Test the default base URL of every Chinese provider."""
        settings = Settings(_env_file=None)
        assert getattr(settings, spec.base_url_attr) == spec.default_base_url

    @pytest.mark.parametrize("spec", CN_PROVIDERS, ids=lambda s: s.key)
    def test_cn_provider_not_configured_without_key(self, spec):
        """Test has_<key> is False while the API key is missing."""
        settings = Settings(_env_file=None)
        assert getattr(settings, spec.has_attr) is False

    @pytest.mark.parametrize("spec", CN_PROVIDERS, ids=lambda s: s.key)
    def test_cn_provider_configured_with_key(self, spec, monkeypatch):
        """Test has_<key> is True once the API key is set."""
        monkeypatch.setenv(spec.api_key_env, f"sk-{spec.key}-test-key-123456")
        settings = Settings(_env_file=None)
        assert getattr(settings, spec.has_attr) is True

    @pytest.mark.parametrize("spec", CN_PROVIDERS, ids=lambda s: s.key)
    def test_cn_provider_base_url_overridable(self, spec, monkeypatch):
        """Test the *_BASE_URL env var overrides the default base URL."""
        monkeypatch.setenv(spec.base_url_env, f"https://proxy.local/{spec.key}")
        settings = Settings(_env_file=None)
        assert getattr(settings, spec.base_url_attr) == f"https://proxy.local/{spec.key}"

    @pytest.mark.parametrize("spec", CN_PROVIDERS, ids=lambda s: s.key)
    def test_cn_provider_get_models(self, spec, monkeypatch):
        """Test parsing the *_MODELS env var of every Chinese provider."""
        monkeypatch.setenv(spec.models_env, ", ".join(spec.sample_models))
        settings = Settings(_env_file=None)
        assert settings.get_models(spec.key) == list(spec.sample_models)

    @pytest.mark.parametrize("spec", CN_PROVIDERS, ids=lambda s: s.key)
    def test_cn_provider_in_available_providers(self, spec, monkeypatch):
        """Test available_providers includes the provider once its key is set."""
        monkeypatch.setenv(spec.api_key_env, f"sk-{spec.key}-test-key-123456")
        settings = Settings(_env_file=None)
        assert spec.key in settings.available_providers

    @pytest.mark.parametrize("spec", CN_PROVIDERS, ids=lambda s: s.key)
    def test_cn_provider_excluded_from_available_providers(self, spec):
        """Test the provider is absent from available_providers without a key."""
        settings = Settings(_env_file=None)
        assert spec.key not in settings.available_providers


def test_env_example_models_match_the_provider_specs():
    """The .env.example model lists must name the models the tests use."""
    from tests.provider_specs import ALL_COMPAT_PROVIDERS, env_example_models

    examples = env_example_models()
    for spec in ALL_COMPAT_PROVIDERS:
        assert examples[spec.env_prefix.lower()] == ",".join(spec.sample_models)


@pytest.mark.parametrize("spec", ALL_COMPAT_PROVIDERS, ids=lambda s: s.key)
def test_env_example_base_url_matches_the_provider_spec(spec):
    """The documented default base URL must be the one the code uses."""
    from pathlib import Path

    from tests.provider_specs import env_example_vars

    example = env_example_vars()
    assert example[spec.base_url_env.lower()] == spec.default_base_url
    text = (Path(__file__).resolve().parent.parent / ".env.example").read_text(encoding="utf-8")
    assert f"# Optional: Override base URL (default: {spec.default_base_url})" in text


@pytest.mark.parametrize("spec", ALL_COMPAT_PROVIDERS, ids=lambda s: s.key)
def test_env_example_documents_every_provider_variable(spec):
    """Every provider needs its three variables in .env.example."""
    from tests.provider_specs import env_example_vars

    example = env_example_vars()
    for var in (spec.api_key_env, spec.models_env, spec.base_url_env):
        assert var.lower() in example


@pytest.mark.parametrize("spec", ALL_COMPAT_PROVIDERS, ids=lambda s: s.key)
def test_readme_base_url_matches_the_provider_spec(spec):
    """The README must point users at the endpoint the code actually uses."""
    from tests.provider_specs import readme_base_urls

    urls = readme_base_urls()
    assert urls[spec.base_url_env.lower()] == spec.default_base_url
