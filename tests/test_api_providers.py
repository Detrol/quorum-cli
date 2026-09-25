"""Tests for API/local providers as MCP participants (no real API calls)."""

from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from quorum.clients.types import SystemMessage, UserMessage


def run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def settings(**kw):
    s = MagicMock()
    s.has_openai, s.openai_api_key = True, "sk-test123456789012345678901234"
    s.has_anthropic, s.anthropic_api_key = False, None
    s.ollama_base_url, s.ollama_api_key = "http://localhost:11434", None
    models = {"openai": ["gpt-5.5"], "anthropic": ["claude-opus-5"]}
    s.get_models.side_effect = lambda p: models.get(p, [])
    s.get_models_with_display_names.side_effect = lambda p: [(m, m.upper()) for m in models.get(p, [])]
    for k, v in kw.items():
        setattr(s, k, v)
    return s


@patch("quorum.models.get_settings")
def test_prefixed_openai_id_passes_effort(mock_settings):
    from quorum.models import _create_model_client_internal

    mock_settings.return_value = settings()
    client = _create_model_client_internal("openai:gpt-5.5@max")
    assert client.model == "gpt-5.5" and client.reasoning_effort == "high"  # clamped


@patch("quorum.models.get_settings")
def test_prefixed_id_must_be_configured(mock_settings):
    from quorum.models import _create_model_client_internal

    mock_settings.return_value = settings()
    with pytest.raises(ValueError, match="OPENAI_MODELS"):
        _create_model_client_internal("openai:gpt-4o")


@patch("quorum.models.get_settings")
def test_ollama_id_drops_effort(mock_settings):
    from quorum.models import _create_model_client_internal

    mock_settings.return_value = settings()
    client = _create_model_client_internal("ollama:qwen3:8b@high")
    assert client.model == "qwen3:8b" and client.reasoning_effort is None


def test_openai_client_sends_reasoning_effort_only_when_set():
    from quorum.clients import OpenAIClient

    for effort, expected in (("low", {"reasoning_effort": "low"}), (None, {})):
        client = OpenAIClient(model="m", api_key="k", reasoning_effort=effort)
        reply = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))])
        client._client = MagicMock()
        client._client.chat.completions.create = AsyncMock(return_value=reply)
        assert run(client.create([UserMessage(content="q")])) == "ok"
        kwargs = client._client.chat.completions.create.call_args.kwargs
        assert {k: kwargs[k] for k in expected} == expected and ("reasoning_effort" in kwargs) == bool(effort)


def test_anthropic_client_effort_uses_adaptive_thinking():
    from quorum.clients import AnthropicClient

    client = AnthropicClient(model="claude-opus-5", api_key="k", effort="xhigh")
    client._client = MagicMock()
    client._client.messages.create = AsyncMock(
        return_value=SimpleNamespace(content=[SimpleNamespace(text="ok")]))
    assert run(client.create([SystemMessage(content="s"), UserMessage(content="q")])) == "ok"
    kwargs = client._client.messages.create.call_args.kwargs
    assert kwargs["output_config"] == {"effort": "xhigh"}
    assert kwargs["thinking"] == {"type": "adaptive"} and kwargs["max_tokens"] == 16000

    plain = AnthropicClient(model="claude-haiku-4-5", api_key="k")
    plain._client = client._client
    run(plain.create([UserMessage(content="q")]))
    assert "output_config" not in plain._client.messages.create.call_args.kwargs


@patch("quorum.providers.discover_ollama_models", new_callable=AsyncMock)
@patch("quorum.providers.get_settings")
def test_api_catalog_follows_env_config(mock_settings, mock_ollama):
    from quorum.providers import api_catalog

    s = settings()
    for p in ("openrouter", "lmstudio", "llamaswap", "custom", "google", "xai"):
        setattr(s, f"has_{p}", False)
    mock_settings.return_value = s
    mock_ollama.return_value = [("ollama:qwen3:8b", "Qwen3 8b")]
    cat = run(api_catalog())
    assert cat["openai"]["status"] == "ok" and cat["openai"]["models"][0]["id"] == "openai:gpt-5.5"
    assert cat["openai"]["models"][0]["efforts"] == ["low", "medium", "high"]
    assert cat["anthropic"]["status"] == "unavailable" and "ANTHROPIC" in cat["anthropic"]["detail"]
    assert cat["ollama"]["kind"] == "local" and cat["ollama"]["models"][0]["model"] == "qwen3:8b"
    assert cat["ollama"]["models"][0]["efforts"] == [] and cat["openai"]["tools"] == "none"


def test_mcp_canonicalizes_bare_ids_and_drops_unsupported_effort():
    import quorum.mcp as m

    catalog = {
        "openai": {"status": "ok", "models": [{"model": "gpt-5.5"}]},
        "ollama": {"status": "ok", "models": [{"model": "qwen3:8b"}]},
        "claude": {"status": "ok", "models": [{"model": "opus"}]},
    }
    with patch.object(m, "get_provider_for_model", lambda mid: "openai" if mid == "gpt-5.5" else None):
        ids = run(m._validate_participants(["claude:opus", "gpt-5.5", "ollama:qwen3:8b"], "high", catalog))
        assert ids == ["claude:opus@high", "openai:gpt-5.5@high", "ollama:qwen3:8b"]
        with pytest.raises(ValueError, match="Unknown model 'gpt-4o'"):
            run(m._validate_participants(["gpt-4o"], None, catalog))


def test_global_config_ignores_cwd_env(tmp_path, monkeypatch):
    from quorum import config

    monkeypatch.chdir(tmp_path)
    Path(".env").write_text("OPENAI_API_KEY=project-key\n")
    monkeypatch.delenv("QUORUM_GLOBAL_CONFIG", raising=False)
    assert config._get_active_env_file() == Path(".env")
    monkeypatch.setenv("QUORUM_GLOBAL_CONFIG", "1")
    assert config._get_active_env_file() == config.CACHE_DIR / ".env"


def test_lineup_form_lists_models_with_efforts_and_remembers_last(tmp_path, monkeypatch):
    import json as _json

    import quorum.mcp as m

    monkeypatch.setattr(m, "LINEUP_FILE", tmp_path / "last_lineup.json")
    catalog = {
        "claude": {"status": "ok", "kind": "agent", "models": [{"model": "opus", "efforts": ["low", "high"]}]},
        "codex": {"status": "unavailable", "kind": "agent", "models": []},
        "ollama": {"status": "ok", "kind": "local", "models": [{"model": "qwen3:8b", "efforts": []}]},
    }
    schema = m._lineup_schema(catalog, "standard")
    assert list(schema["properties"]) == ["claude", "ollama", "method"]
    claude = schema["properties"]["claude"]
    assert claude["enum"] == ["off", "opus", "opus@low", "opus@high"] and claude["default"] == "off"
    assert claude["enumNames"][1] == "opus · default effort"
    assert "no project or web access" in schema["properties"]["ollama"]["title"]

    (tmp_path / "last_lineup.json").write_text(
        _json.dumps({"participants": ["claude:opus@high", "ollama:qwen3:8b"], "method": "tradeoff"}))
    schema = m._lineup_schema(catalog, "standard")
    assert schema["properties"]["claude"]["default"] == "opus@high"
    assert schema["properties"]["ollama"]["default"] == "qwen3:8b"
    assert schema["properties"]["method"]["default"] == "tradeoff"


def test_count_problem():
    import quorum.mcp as m

    assert m._count_problem(1, "standard") and m._count_problem(2, "advocate")
    assert m._count_problem(3, "oxford") and m._count_problem(2, "oxford") is None
    assert m._count_problem(3, "delphi") is None
