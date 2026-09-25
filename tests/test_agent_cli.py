"""Tests for agent CLI participants (no real agent CLIs are called)."""

import asyncio
import json
import os
import stat
import time

import pytest

from quorum.clients import agent_cli as ac
from quorum.clients.types import SystemMessage, UserMessage


def run(coro):
    """Run on a private loop; run() would unset the loop other tests rely on."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@pytest.fixture(autouse=True)
def isolated_homes(tmp_path, monkeypatch):
    """Keep every test away from the real ~/.quorum isolation homes and login files."""
    monkeypatch.setattr(ac, "HOMES_DIR", tmp_path / "homes")


def test_parse_participant():
    p = ac.parse_participant("claude:opus@high")
    assert (p.agent, p.model, p.effort, p.id) == ("claude", "opus", "high", "claude:opus@high")
    assert ac.parse_participant("codex:gpt-6-sol", "low").effort == "low"
    assert ac.parse_participant("agy:gemini-3.1-pro-high").effort is None
    assert ac.parse_participant("openai:gpt-4o@high").agent == "openai"
    assert ac.parse_participant("ollama:qwen3:8b").model == "qwen3:8b"
    for bad in ("gpt-4o", "mistral:x", "claude:", "claude:opus@huge", "codex:-rf"):
        with pytest.raises(ValueError):
            ac.parse_participant(bad)
    assert ac.is_agent_model("codex:x") and not ac.is_agent_model("ollama:llama3")


def test_clamp_effort():
    assert ac.clamp_effort("max", ["low", "medium", "high"]) == "high"
    assert ac.clamp_effort("xhigh", ["low", "high", "max"]) == "high"
    assert ac.clamp_effort("low", ["medium", "high"]) == "medium"
    assert ac.clamp_effort("medium", ["low", "medium"]) == "medium"
    assert ac.clamp_effort(None, ["low"]) is None


def test_parse_codex_models_roles_by_priority():
    raw = json.dumps({"models": [
        {"slug": "sol", "priority": 2, "visibility": "list", "description": "Workhorse",
         "supported_reasoning_levels": [{"effort": "low"}, {"effort": "max"}], "default_reasoning_level": "low"},
        {"slug": "hidden", "priority": 0, "visibility": "hide"},
        {"slug": "astra", "priority": 1, "visibility": "list", "supported_reasoning_levels": ["high"]},
        {"slug": "luna", "priority": 3, "visibility": "list"},
        {"slug": "old", "priority": 9, "visibility": "list"},
    ]})
    models = ac._parse_codex_models(raw)
    assert [(m["model"], m["role"]) for m in models] == [
        ("astra", "flagship"), ("sol", "workhorse"), ("luna", "fast"), ("old", None)]
    assert models[1]["efforts"] == ["low", "max"] and models[0]["efforts"] == ["high"]


def test_parse_agy_models_groups_effort_variants():
    raw = ("Fetching available models...\n"
           "gemini-3.8-flash-high\tGemini 3.8 Flash (High)\ngemini-3.8-flash-low\tGemini 3.8 Flash (Low)\n"
           "gemini-3.8-flash-medium\tGemini 3.8 Flash (Medium)\ngemini-3.7-flash-high\tOld\n"
           "gemini-3.1-pro-high\tGemini 3.1 Pro (High)\ngemini-3.1-pro-low\tGemini 3.1 Pro (Low)\n"
           "claude-sonnet-4-6\tClaude Sonnet 4.6 (Thinking)\n")
    models = {m["model"]: m for m in ac._parse_agy_models(raw)}
    assert list(models) == ["gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.1-pro", "claude-sonnet-4-6"]
    assert models["gemini-3.8-flash"]["efforts"] == ["low", "medium", "high"]
    assert models["gemini-3.8-flash"]["description"] == "Gemini 3.8 Flash"
    assert models["gemini-3.1-pro"]["efforts"] == ["low", "high"]
    assert models["claude-sonnet-4-6"]["efforts"] == []
    assert models["gemini-3.1-pro"]["role"] == "flagship" and models["gemini-3.8-flash"]["role"] == "workhorse"


def test_agy_effort_selects_model_variant():
    assert ac.agy_model_id("gemini-3.1-pro", "xhigh", ["low", "high"]) == "gemini-3.1-pro-high"
    assert ac.agy_model_id("gemini-3.1-pro", "medium", ["low", "high"]) == "gemini-3.1-pro-low"
    assert ac.agy_model_id("gemini-3.8-flash", None, ["low", "medium", "high"]) == "gemini-3.8-flash-medium"
    assert ac.agy_model_id("gemini-3.1-pro-high", "low", ["low", "high"]) == "gemini-3.1-pro-high"
    assert ac.agy_model_id("claude-sonnet-4-6", "high", []) == "claude-sonnet-4-6"
    assert ac.base_model(ac.Participant("agy", "gemini-3.1-pro-high")) == "gemini-3.1-pro"


def test_parse_grok_models_default_first():
    raw = "You are logged in with grok.com.\n\nAvailable models:\n  - grok-4.6-fast\n  * grok-4.7 (default)\n"
    models = ac._parse_grok_models(raw)
    assert [m["model"] for m in models] == ["grok-4.7", "grok-4.6-fast"]
    assert models[0]["efforts"] == ["low", "medium", "high", "xhigh"]


def test_render_prompt_has_preamble_role_and_task():
    text = ac.render_prompt([SystemMessage(content="Be the critic"), UserMessage(content="Q?")])
    assert text.startswith(ac.PARTICIPANT_PREAMBLE)
    assert "## Your role\nBe the critic" in text and text.endswith("## Task\nQ?")


@pytest.fixture
def fake_claude(tmp_path, monkeypatch):
    """A fake `claude` on PATH that echoes its stdin prompt back as JSON."""
    script = tmp_path / "claude"
    script.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, sys\n"
        "prompt = sys.stdin.read()\n"
        "if 'SLEEP' in prompt:\n"
        "    import time; time.sleep(30)\n"
        "print(json.dumps({'result': f\"{os.environ['QUORUM_PARTICIPANT']}|{sys.argv[1:]}|{prompt}\","
        " 'is_error': 'FAIL' in prompt}))\n"
    )
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")
    return script


def test_call_participant_claude_isolated_read_only(fake_claude, tmp_path):
    p = ac.Participant("claude", "opus", "xhigh")
    reply = run(ac.call_participant(p, "hello", str(tmp_path)))
    marker, argv, prompt = reply.split("|", 2)
    assert marker == "1" and prompt == "hello"
    assert "'--setting-sources', ''" in argv and "'--strict-mcp-config'" in argv
    assert f"'--tools', '{ac.CLAUDE_TOOLS}'" in argv and "'--effort', 'xhigh'" in argv


def test_call_participant_error_and_timeout_kill(fake_claude, tmp_path):
    p = ac.Participant("claude", "opus")
    with pytest.raises(RuntimeError, match="claude error"):
        run(ac.call_participant(p, "FAIL", str(tmp_path)))
    start = time.monotonic()
    with pytest.raises(asyncio.TimeoutError):
        run(ac.call_participant(p, "SLEEP", str(tmp_path), timeout=0.5))
    assert time.monotonic() - start < 5


def test_client_records_dropped_participant(fake_claude, tmp_path, monkeypatch):
    monkeypatch.setattr(ac, "load_cached_catalog", lambda: None)
    client = ac.AgentCLIClient("claude:opus@low")

    async def scenario():
        failed: dict[str, str] = {}
        ac.RUN_FAILED.set(failed)
        ac.RUN_CWD.set(str(tmp_path))
        assert "ok" in await client.create([UserMessage(content="ok")])
        with pytest.raises(RuntimeError):
            await client.create([UserMessage(content="FAIL")])
        with pytest.raises(RuntimeError, match="dropped earlier"):
            await client.create([UserMessage(content="ok again")])
        return failed

    assert list(run(scenario())) == ["claude:opus@low"]


def test_call_participant_grok_read_only_isolated(tmp_path, monkeypatch):
    """A fake `grok` that reports its argv, env and prompt file back as JSON."""
    script = tmp_path / "grok"
    script.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, sys\n"
        "a = sys.argv[1:]\n"
        "prompt = open(a[a.index('--prompt-file') + 1]).read()\n"
        "text = json.dumps({'argv': a, 'home': os.environ['HOME'], 'prompt': prompt,"
        " 'compat': os.environ.get('GROK_CLAUDE_MCPS_ENABLED')})\n"
        "print(json.dumps({'text': text, 'stopReason': 'end_turn'}))\n"
    )
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")

    p = ac.Participant("grok", "grok-4.7", "max")
    info = json.loads(run(ac.call_participant(p, "hi", str(tmp_path))))
    argv = info["argv"]
    assert info["prompt"] == "hi" and info["compat"] == "0"
    assert info["home"] == str(tmp_path / "homes" / "grok")
    assert argv[argv.index("--tools") + 1] == ac.GROK_TOOLS
    assert "WebFetch" in argv and argv[argv.index("--effort") + 1] == "xhigh"  # max clamps to xhigh
    assert not list((tmp_path / "homes" / "grok").glob("prompt-*"))  # prompt file cleaned up


def test_sync_login_hands_rotated_token_back(tmp_path):
    real = tmp_path / "real" / "auth.json"
    real.parent.mkdir()
    real.write_text("old token")
    link = tmp_path / "home" / "auth.json"

    ac._sync_login(real, link)
    assert link.is_symlink() and link.read_text() == "old token"

    # The CLI saves a rotated token by rename, replacing our symlink with a newer regular file
    link.unlink()
    link.write_text("rotated token")
    ac._sync_login(real, link)
    assert link.is_symlink() and real.read_text() == "rotated token"
    assert oct(real.stat().st_mode & 0o777) == "0o600"

    # A stale regular file (older than the real login) is dropped, not copied back
    link.unlink()
    link.write_text("stale")
    os.utime(link, (1, 1))
    ac._sync_login(real, link)
    assert real.read_text() == "rotated token" and link.is_symlink()
