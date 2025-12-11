"""Pytest fixtures for Quorum tests."""

from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock

import pytest


@dataclass
class MockModelResponse:
    """Mock response from AI model."""
    content: str
    source: str = "mock-model"


@pytest.fixture
def mock_model_client():
    """Mock AI model client for testing without API calls."""
    client = AsyncMock()
    client.create.return_value = MockModelResponse(content="Mock response")
    return client


@pytest.fixture
def mock_settings(monkeypatch):
    """Mock settings with no API keys (for unit tests)."""
    mock = MagicMock()
    mock.openai_api_key = None
    mock.anthropic_api_key = None
    mock.google_api_key = None
    mock.xai_api_key = None
    mock.openai_models = ""
    mock.anthropic_models = ""
    mock.google_models = ""
    mock.xai_models = ""
    mock.synthesizer_mode = "first"
    mock.rounds_per_agent = 2
    mock.discussion_method = "standard"
    mock.default_language = None
    mock.available_providers = []
    mock.get_models.return_value = []
    mock.get_models_with_display_names.return_value = []
    mock.has_openai = False
    mock.has_anthropic = False
    mock.has_google = False
    mock.has_xai = False

    monkeypatch.setattr("quorum.config.get_settings", lambda: mock)
    return mock


@pytest.fixture
def temp_cache_dir(tmp_path, monkeypatch):
    """Use temporary directory for cache files."""
    cache_dir = tmp_path / ".quorum"
    monkeypatch.setattr("quorum.config.CACHE_DIR", cache_dir)
    monkeypatch.setattr("quorum.config.VALIDATED_MODELS_CACHE", cache_dir / "validated_models.json")
    monkeypatch.setattr("quorum.config.USER_SETTINGS_CACHE", cache_dir / "settings.json")
    monkeypatch.setattr("quorum.config.INPUT_HISTORY_CACHE", cache_dir / "history.json")
    return cache_dir


@pytest.fixture
def mock_openai_response():
    """Create a mock OpenAI-style response."""
    def _create(content: str = "Test response"):
        response = MagicMock()
        response.choices = [MagicMock()]
        response.choices[0].message.content = content
        return response
    return _create


@pytest.fixture
def mock_anthropic_response():
    """Create a mock Anthropic-style response."""
    def _create(content: str = "Test response"):
        response = MagicMock()
        response.content = [MagicMock()]
        response.content[0].text = content
        return response
    return _create


# Markers for test categorization
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "live: marks tests as requiring live API keys (deselect with '-m \"not live\"')"
    )
