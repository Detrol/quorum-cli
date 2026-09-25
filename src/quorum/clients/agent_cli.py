"""Agent CLI participants: claude, codex, agy (Antigravity) and grok as discussion members.

Each call runs the agent headless on the user's own subscription, read-only with web
search, and isolated from the user's agent configuration (hooks, plugins, skills,
MCP servers, memory and instruction files). Invocations are documented and verified
in docs/agent-participants.md.

Participant ids look like ``agent:model@effort``, e.g. ``claude:opus@high``.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import signal
import time
import uuid
from contextlib import suppress
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..config import CACHE_DIR
from .types import Message, SystemMessage, UserMessage

AGENTS = ("claude", "codex", "agy", "grok")
EFFORTS = ("low", "medium", "high", "xhigh", "max")
AGENT_EFFORTS = {
    "claude": list(EFFORTS),
    "codex": ["low", "medium", "high", "xhigh"],  # fallback when the catalog is missing
    "agy": [],  # agy has no effort flag; effort picks the -low/-medium/-high model variant
    "grok": ["low", "medium", "high", "xhigh"],
}
PRESETS = {"quick": ("fast", "low"), "balanced": ("workhorse", "medium"), "deep": ("flagship", "high")}

CATALOG_FILE = CACHE_DIR / "agent_catalog.json"
CATALOG_TTL = 3600
HOMES_DIR = CACHE_DIR / "agent-homes"
AGY_MAX_ARG = 100_000  # Linux caps one argv string at 128 KiB

# Set by the MCP run registry for the duration of one Run.
RUN_CWD: ContextVar[str | None] = ContextVar("quorum_run_cwd", default=None)
RUN_FAILED: ContextVar[dict[str, str] | None] = ContextVar("quorum_run_failed", default=None)

PARTICIPANT_PREAMBLE = (
    "You are one participant in a structured multi-model discussion. You may read files in "
    "the working directory and search the web to ground your answer in current facts rather "
    "than only your training data; cite sources (URLs or file paths) for factual claims. You "
    "must not modify anything. Reply with your contribution only."
)

CLAUDE_TOOLS = "Read,Grep,Glob,WebSearch,WebFetch"
CLAUDE_MODELS = [
    ("fable", "flagship", "Most capable Claude model; heaviest on quota."),
    ("opus", None, "Frontier Claude model for hard reasoning and code."),
    ("sonnet", "workhorse", "Balanced Claude model for everyday work."),
    ("haiku", "fast", "Fast, cheap Claude model for easier tasks."),
]
AGY_SETTINGS = {
    "permissions": {
        "allow": ["read_file(*)", "list_dir(*)", "search_files(*)", "grep(*)",
                  "read_url(*)", "web_search(*)"],
        # Headless agy aborts the whole answer on an unlisted tool; explicit deny lets it continue.
        "deny": ["command(*)", "write_file(*)", "edit_file(*)"],
    }
}
GROK_TOOLS = "read_file,list_dir,grep,web_fetch"
# Headless grok cancels the turn on any permission prompt; web_fetch prompts outside a built-in
# domain allowlist, so allow it everywhere. Only the read tools above exist, so nothing can write.
GROK_ALLOW = ["read_file", "list_dir", "grep", "WebFetch"]
# grok imports other harnesses' project config (rules, skills, MCP servers, hooks) from the cwd.
GROK_COMPAT_OFF = {
    f"GROK_{h}_{k}_ENABLED": "0"
    for h in ("CLAUDE", "CODEX", "CURSOR")
    for k in ("AGENTS", "HOOKS", "MCPS", "RULES", "SKILLS", "SESSIONS")
}
_MODEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/\-\[\]]*$")


@dataclass(frozen=True)
class Participant:
    agent: str
    model: str
    effort: str | None = None

    @property
    def id(self) -> str:
        return f"{self.agent}:{self.model}" + (f"@{self.effort}" if self.effort else "")


def is_agent_model(model_id: str) -> bool:
    agent, sep, _ = model_id.partition(":")
    return bool(sep) and agent in AGENTS


def parse_participant(pid: str, default_effort: str | None = None) -> Participant:
    agent, sep, rest = pid.partition(":")
    model, _, effort = rest.partition("@")
    if not sep or agent not in AGENTS or not _MODEL_RE.match(model):
        raise ValueError(
            f"Invalid participant '{pid}': use agent:model[@effort] with agent one of {', '.join(AGENTS)}"
        )
    effort = effort or default_effort
    if effort and effort not in EFFORTS:
        raise ValueError(f"Invalid effort '{effort}' in '{pid}': use one of {', '.join(EFFORTS)}")
    return Participant(agent, model, effort or None)


def clamp_effort(effort: str | None, supported: list[str]) -> str | None:
    """Nearest supported level at or below the request, else the lowest supported."""
    levels = [e for e in EFFORTS if e in supported]
    if not effort or not levels or effort in levels:
        return effort
    below = [e for e in levels if EFFORTS.index(e) <= EFFORTS.index(effort)]
    return below[-1] if below else levels[0]


def supported_efforts(p: Participant, catalog: dict | None = None) -> list[str]:
    for m in ((catalog or {}).get(p.agent) or {}).get("models", []):
        if m["model"] == p.model and m.get("efforts"):
            return m["efforts"]
    return AGENT_EFFORTS[p.agent]


def render_prompt(messages: list[Message]) -> str:
    parts = [PARTICIPANT_PREAMBLE]
    for msg in messages:
        if isinstance(msg, SystemMessage):
            parts.append(f"## Your role\n{msg.content}")
        elif isinstance(msg, UserMessage):
            parts.append(f"## Task\n{msg.content}")
        else:
            parts.append(f"## Earlier reply\n{msg.content}")
    return "\n\n".join(parts)


# ─────────────────────────────────────────────────────────────
# Isolation homes
# ─────────────────────────────────────────────────────────────


def _sync_login(real: Path, link: Path) -> None:
    """Point an isolation home at the user's real login file.

    CLIs that save a refreshed token by renaming a new file into place (grok does) replace our
    symlink with a regular file holding the only valid, rotated token. Copy that back over the
    real login first, then relink, so the isolated and the user's own CLI both keep working.
    """
    if link.exists() and not link.is_symlink():
        if not real.exists() or link.stat().st_mtime >= real.stat().st_mtime:
            real.parent.mkdir(parents=True, exist_ok=True)
            tmp = real.with_name(real.name + ".quorum-tmp")
            shutil.copy2(link, tmp)
            tmp.chmod(0o600)
            os.replace(tmp, real)
        link.unlink()
    if real.exists() and not link.is_symlink():
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(real)


def _login_files() -> list[tuple[Path, Path]]:
    """(real login file, its link in an isolation home) for every Agent that needs one."""
    home, gem = Path.home(), Path.home() / ".gemini"
    codex = Path(os.environ.get("CODEX_HOME") or home / ".codex")
    agy = HOMES_DIR / "agy" / ".gemini"
    return [
        (codex / "auth.json", HOMES_DIR / "codex" / "auth.json"),
        *[(gem / n, agy / n) for n in ("oauth_creds.json", "google_accounts.json", "installation_id")],
        (gem / "antigravity-cli" / "installation_id", agy / "antigravity-cli" / "installation_id"),
        (home / ".grok" / "auth.json", HOMES_DIR / "grok" / ".grok" / "auth.json"),
    ]


def _resync_logins() -> None:
    """Run after every agent process: hand refreshed tokens back to the real login at once.

    ponytail: races the user's own CLI refreshing in the same instant; a file lock shared with
    each CLI would close it, but no CLI documents one.
    """
    for real, link in _login_files():
        if link.parent.is_dir():
            _sync_login(real, link)


def _codex_home() -> Path:
    """CODEX_HOME with only the login: no config, hooks, plugins or global AGENTS.md."""
    home = HOMES_DIR / "codex"
    home.mkdir(parents=True, exist_ok=True)
    _resync_logins()
    return home


def _agy_home() -> Path:
    """HOME for agy with only the OAuth files and a read-only permission policy."""
    home = HOMES_DIR / "agy"
    cli = home / ".gemini" / "antigravity-cli"
    cli.mkdir(parents=True, exist_ok=True)
    _resync_logins()
    (cli / "settings.json").write_text(json.dumps(AGY_SETTINGS))
    return home


def _grok_home() -> Path:
    """HOME for grok with only its login: no rules, skills, plugins, hooks or MCP servers.

    It has no trusted folders, so grok treats every project as untrusted and skips the project's
    own .grok/ config, .mcp.json, rules and AGENTS.md. Never add trusted folders here.
    """
    home = HOMES_DIR / "grok"
    (home / ".grok").mkdir(parents=True, exist_ok=True)
    _resync_logins()
    return home


def _grok_env() -> dict[str, str]:
    return _base_env() | GROK_COMPAT_OFF | {"HOME": str(_grok_home())}


def _base_env() -> dict[str, str]:
    return {**os.environ, "QUORUM_PARTICIPANT": "1"}


# ─────────────────────────────────────────────────────────────
# Invocation
# ─────────────────────────────────────────────────────────────


async def _run(
    cmd: list[str], env: dict[str, str], cwd: str, stdin: str | None = None, timeout: float | None = None
) -> tuple[int, str, str]:
    """Run a command; kill its whole process group on timeout or cancellation."""
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=cwd,
        env=env,
        stdin=asyncio.subprocess.PIPE if stdin is not None else asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        start_new_session=True,
    )
    try:
        out, err = await asyncio.wait_for(
            proc.communicate(stdin.encode() if stdin is not None else None), timeout
        )
    except BaseException:
        with suppress(ProcessLookupError):
            os.killpg(proc.pid, signal.SIGKILL)
        with suppress(BaseException):
            await asyncio.shield(proc.wait())
        raise
    finally:
        _resync_logins()
    return proc.returncode or 0, out.decode(errors="replace"), err.decode(errors="replace")


def _tail(text: str, n: int = 300) -> str:
    text = text.strip()
    return text[-n:] if len(text) > n else text


async def call_participant(
    p: Participant, prompt: str, cwd: str, catalog: dict | None = None, timeout: float | None = None
) -> str:
    """Send one prompt to one Participant and return its reply text."""
    if shutil.which(p.agent) is None:
        raise RuntimeError(f"{p.agent} is not installed")
    effort = clamp_effort(p.effort, supported_efforts(p, catalog))
    env = _base_env()

    if p.agent == "claude":
        cmd = ["claude", "-p", "--model", p.model, "--setting-sources", "",
               "--strict-mcp-config", "--disable-slash-commands", "--no-session-persistence",
               "--tools", CLAUDE_TOOLS, "--allowedTools", CLAUDE_TOOLS, "--output-format", "json"]
        if effort:
            cmd += ["--effort", effort]
        env |= {"CLAUDE_CODE_DISABLE_CLAUDE_MDS": "1", "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"}
        code, out, err = await _run(cmd, env, cwd, stdin=prompt, timeout=timeout)
        try:
            data = json.loads(out)
        except json.JSONDecodeError:
            raise RuntimeError(f"claude failed (exit {code}): {_tail(err or out)}") from None
        if data.get("is_error") or code:
            raise RuntimeError(f"claude error: {_tail(str(data.get('result') or err))}")
        return str(data.get("result") or "")

    if p.agent == "codex":
        out_file = HOMES_DIR / f"codex-out-{uuid.uuid4().hex}.txt"
        cmd = ["codex", "--search", "exec", "-m", p.model, "-c", "project_doc_max_bytes=0",
               "-s", "read-only", "--skip-git-repo-check", "--ephemeral", "--color", "never",
               "-o", str(out_file), "-"]
        if effort:
            cmd[5:5] = ["-c", f"model_reasoning_effort={effort}"]
        env["CODEX_HOME"] = str(_codex_home())
        try:
            code, out, err = await _run(cmd, env, cwd, stdin=prompt, timeout=timeout)
            reply = out_file.read_text() if out_file.exists() else ""
        finally:
            out_file.unlink(missing_ok=True)
        if code or not reply.strip():
            raise RuntimeError(f"codex failed (exit {code}): {_tail(err or out)}")
        return reply

    if p.agent == "grok":
        env = _grok_env()
        prompt_file = HOMES_DIR / "grok" / f"prompt-{uuid.uuid4().hex}.md"
        prompt_file.write_text(prompt)
        cmd = ["grok", "--prompt-file", str(prompt_file), "--model", p.model, "--tools", GROK_TOOLS,
               "--no-subagents", "--output-format", "json"]
        for rule in GROK_ALLOW:
            cmd += ["--allow", rule]
        if effort:
            cmd += ["--effort", effort]
        try:
            code, out, err = await _run(cmd, env, cwd, timeout=timeout)
        finally:
            prompt_file.unlink(missing_ok=True)
        try:
            data = json.loads(out[out.index("{"):])
        except ValueError:
            raise RuntimeError(f"grok failed (exit {code}): {_tail(err or out)}") from None
        if data.get("stopReason") != "end_turn" or not data.get("text"):
            detail = data.get("message") or data.get("stopReason") or err or out
            raise RuntimeError(f"grok error: {_tail(str(detail))}")
        return str(data["text"])

    # agy takes the prompt as an argument; oversized prompts go through a file it may read.
    home = _agy_home()
    prompt_file = None
    model = agy_model_id(p.model, p.effort, supported_efforts(p, catalog))
    cmd = ["agy", "--model", model, "--sandbox", "--add-dir", cwd, "--output-format", "json"]
    if len(prompt.encode()) > AGY_MAX_ARG:
        prompt_file = home / f"prompt-{uuid.uuid4().hex}.md"
        prompt_file.write_text(prompt)
        cmd += ["--add-dir", str(home)]
        prompt = f"Read your full instructions from {prompt_file} and follow them exactly."
    cmd.append(f"--print={prompt}")
    env["HOME"] = str(home)
    try:
        code, out, err = await _run(cmd, env, cwd, timeout=timeout)
    finally:
        if prompt_file:
            prompt_file.unlink(missing_ok=True)
    try:
        data = json.loads(out[out.index("{"):])
    except ValueError:
        raise RuntimeError(f"agy failed (exit {code}): {_tail(err or out)}") from None
    if data.get("status") != "SUCCESS" or not data.get("response"):
        raise RuntimeError(f"agy error: {_tail(str(data.get('error') or err or out))}")
    return str(data["response"])


class AgentCLIClient:
    """ChatClient that routes a Participant id to its agent CLI."""

    def __init__(self, model_id: str):
        self.model = model_id
        self.participant = parse_participant(model_id)

    async def create(self, messages: list[Message]) -> str:
        failed = RUN_FAILED.get()
        if failed is not None and self.model in failed:
            raise RuntimeError(f"dropped earlier in this run: {failed[self.model]}")
        try:
            return await call_participant(
                self.participant, render_prompt(messages), RUN_CWD.get() or os.getcwd(),
                catalog=load_cached_catalog(),
            )
        except BaseException as e:
            if failed is not None:
                reason = "timed out" if isinstance(e, asyncio.CancelledError) else str(e)[:300]
                failed.setdefault(self.model, reason)
            raise


# ─────────────────────────────────────────────────────────────
# Catalog discovery
# ─────────────────────────────────────────────────────────────


def load_cached_catalog() -> dict | None:
    try:
        return json.loads(CATALOG_FILE.read_text())["agents"]
    except (OSError, ValueError, KeyError):
        return None


def _model(agent: str, model: str, description: str, role: str | None,
           efforts: list[str], default: str | None = None) -> dict[str, Any]:
    return {"id": f"{agent}:{model}", "model": model, "description": description,
            "role": role, "efforts": efforts, "default_effort": default}


def _parse_codex_models(raw: str) -> list[dict]:
    data = json.loads(raw)
    listed = [m for m in data.get("models", data) if m.get("visibility") == "list"]
    listed.sort(key=lambda m: m.get("priority", 999))
    roles = ["flagship", "workhorse", "fast"]  # ponytail: priority order 1/2/3, revisit if codex reorders tiers
    return [
        _model("codex", m["slug"], m.get("description", ""), roles[i] if i < 3 else None,
               [e["effort"] if isinstance(e, dict) else e for e in m.get("supported_reasoning_levels", [])],
               m.get("default_reasoning_level"))
        for i, m in enumerate(listed)
    ]


_AGY_EFFORT_SUFFIX = re.compile(r"-(low|medium|high)$")


def _parse_agy_models(raw: str) -> list[dict]:
    """Group `agy models` variants by base: `gemini-3.8-flash-{low,medium,high}` → one model
    `gemini-3.8-flash` whose efforts are the variants. Listing is newest-first."""
    bases: dict[str, dict] = {}
    for line in raw.splitlines():
        if "\t" not in line:
            continue
        mid, name = (part.strip() for part in line.split("\t", 1))
        suffix = _AGY_EFFORT_SUFFIX.search(mid)
        base = mid[: suffix.start()] if suffix else mid
        label = re.sub(r"\s*\((Low|Medium|High)\)$", "", name)
        m = bases.setdefault(base, _model("agy", base, label, None, []))
        if suffix and suffix.group(1) not in m["efforts"]:
            m["efforts"].append(suffix.group(1))
    models = list(bases.values())
    for m in models:
        m["efforts"].sort(key=EFFORTS.index)
    # ponytail: newest gemini pro is flagship, newest gemini flash is workhorse (and fast at low effort)
    for role, kind in (("flagship", "-pro"), ("workhorse", "-flash")):
        m = next((m for m in models if m["model"].startswith("gemini") and kind in m["model"]), None)
        if m:
            m["role"] = role
    return models


def base_model(p: Participant) -> str:
    """The catalog id for a Participant: agy variant ids map to their base."""
    return _AGY_EFFORT_SUFFIX.sub("", p.model) if p.agent == "agy" else p.model


def agy_model_id(model: str, effort: str | None, efforts: list[str]) -> str:
    """The concrete agy model for a base + effort; full variant ids pass through unchanged."""
    if _AGY_EFFORT_SUFFIX.search(model) or not efforts:
        return model
    return f"{model}-{clamp_effort(effort or 'medium', efforts)}"


def _parse_grok_models(raw: str) -> list[dict]:
    """`grok models` lists `* id (default)` / `- id`; the default comes first."""
    rows = re.findall(r"^\s*([*-])\s+(\S+)", raw, flags=re.M)
    rows.sort(key=lambda r: r[0] != "*")
    return [_model("grok", mid, "Default grok model." if mark == "*" else "", None, AGENT_EFFORTS["grok"])
            for mark, mid in rows]


async def _discover_one(agent: str) -> dict[str, Any]:
    if shutil.which(agent) is None:
        return {"status": "unavailable", "detail": "not installed", "models": []}
    cwd = str(Path.home())
    try:
        if agent == "claude":
            code, out, _ = await _run(["claude", "auth", "status"], _base_env(), cwd, timeout=20)
            logged_in = code == 0 and json.loads(out).get("loggedIn")
            return {
                "status": "ok" if logged_in else "unavailable",
                "detail": "logged in" if logged_in else "not logged in (run: claude auth login)",
                "models": [_model("claude", m, d, r, AGENT_EFFORTS["claude"]) for m, r, d in CLAUDE_MODELS],
            }
        if agent == "codex":
            code, _, _ = await _run(["codex", "login", "status"], _base_env(), cwd, timeout=20)
            if code:
                return {"status": "unavailable", "detail": "not logged in (run: codex login)", "models": []}
            code, out, err = await _run(["codex", "debug", "models"], _base_env(), cwd, timeout=30)
            if code:
                return {"status": "unavailable", "detail": _tail(err), "models": []}
            return {"status": "ok", "detail": "logged in", "models": _parse_codex_models(out)}
        if agent == "grok":
            # Listing models needs a login; the first call can race a token refresh, so retry once.
            for _ in range(2):
                code, out, err = await _run(["grok", "models"], _grok_env(), cwd, timeout=30)
                if "logged in" in out:
                    break
            models = _parse_grok_models(out) if "logged in" in out else []
            if not models:
                return {"status": "unavailable", "detail": "not logged in (run: grok login)", "models": []}
            return {"status": "ok", "detail": "logged in", "models": models}
        # agy: listing models requires a working login, so it doubles as the auth check.
        env = _base_env() | {"HOME": str(_agy_home())}
        code, out, err = await _run(["agy", "models"], env, cwd, timeout=30)
        models = _parse_agy_models(out)
        if code or not models:
            return {"status": "unavailable", "detail": _tail(err or out) or "no models", "models": []}
        return {"status": "ok", "detail": "logged in", "models": models}
    except (asyncio.TimeoutError, OSError, ValueError) as e:
        return {"status": "unavailable", "detail": f"discovery failed: {e!s}"[:300], "models": []}


async def discover(refresh: bool = False) -> dict[str, dict]:
    """Catalog of every Agent: status, models, efforts and roles. Cached for an hour."""
    if not refresh:
        try:
            cached = json.loads(CATALOG_FILE.read_text())
            if time.time() - cached["at"] < CATALOG_TTL:
                return cached["agents"]
        except (OSError, ValueError, KeyError):
            pass
    agents = dict(zip(AGENTS, await asyncio.gather(*(_discover_one(a) for a in AGENTS))))
    CATALOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CATALOG_FILE.write_text(json.dumps({"at": time.time(), "agents": agents}))
    return agents


def resolve_preset(name: str, catalog: dict[str, dict], agents: list[str] | None = None) -> list[str]:
    """One Participant per available Agent (optionally only `agents`), by role; claude first
    so it writes the Synthesis."""
    if name not in PRESETS:
        raise ValueError(f"Unknown preset '{name}': use one of {', '.join(PRESETS)}")
    unknown = set(agents or ()) - set(AGENTS)
    if unknown:
        raise ValueError(f"Unknown agents {sorted(unknown)}: use any of {', '.join(AGENTS)}")
    role, effort = PRESETS[name]
    out = []
    for agent in AGENTS:
        if agents and agent not in agents:
            continue
        entry = catalog.get(agent) or {}
        if entry.get("status") != "ok" or not entry["models"]:
            continue
        # Agents without role tiers (grok lists a single default model) fall back to their first model.
        m = next((m for m in entry["models"] if m["role"] == role), None) or next(
            (m for m in entry["models"] if m["role"] == "workhorse"), entry["models"][0])
        out.append(f"{agent}:{m['model']}@{clamp_effort(effort, m['efforts'])}")
    return out


async def ping(agent: str, catalog: dict[str, dict], timeout: float = 120) -> dict[str, Any]:
    """Real round trip with the Agent's fast model at low effort."""
    entry = catalog.get(agent) or {}
    if entry.get("status") != "ok":
        return {"ok": False, "detail": entry.get("detail", "unavailable")}
    fast = next((m for m in entry["models"] if m["role"] == "fast"), None) or next(
        (m for m in entry["models"] if m["role"] == "workhorse"), entry["models"][0])
    p = Participant(agent, fast["model"], clamp_effort("low", fast["efforts"]))
    start = time.monotonic()
    try:
        reply = await call_participant(p, "Reply with exactly one word: pong", str(Path.home()),
                                       catalog, timeout=timeout)
    except Exception as e:
        return {"ok": False, "participant": p.id, "detail": str(e)[:300] or type(e).__name__}
    return {"ok": "pong" in reply.lower(), "participant": p.id,
            "seconds": round(time.monotonic() - start, 1), "reply": reply.strip()[:80]}
