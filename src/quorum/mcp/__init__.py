"""MCP server for Quorum: discussions between agent CLIs (claude, codex, agy).

Tools: quorum_list_models, quorum_start, quorum_wait, quorum_check.
A Run executes inside this server process; the caller waits on it in slices so long
discussions survive MCP client tool timeouts. Terms: see CONTEXT.md.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
from dataclasses import asdict, dataclass, field, is_dataclass
from pathlib import Path
from typing import Any

import mcp.server.stdio
import mcp.types as types
from mcp.server.lowlevel import NotificationOptions, Server
from mcp.server.models import InitializationOptions

from quorum.clients.agent_cli import (
    AGENTS,
    EFFORTS,
    PRESETS,
    RUN_CWD,
    RUN_FAILED,
    discover,
    parse_participant,
    ping,
    resolve_preset,
)
from quorum.config import CACHE_DIR
from quorum.constants import __version__
from quorum.methods.base import TURN_TIMEOUT

# Limits for file reading
MAX_FILES = 10
MAX_FILE_SIZE = 100_000  # 100KB per file
MAX_TOTAL_CONTEXT = 500_000  # 500KB total

# Run limits (overridable per quorum_start call)
DEFAULT_MAX_PARTICIPANTS = 4
DEFAULT_TURN_MINUTES = 10
DEFAULT_TOTAL_MINUTES = 30
WAIT_DEFAULT_SECONDS = 45  # stays under Codex's default MCP tool timeout
WAIT_MAX_SECONDS = 600
RUNS_DIR = CACHE_DIR / "runs"
METHOD_MIN = {"advocate": 3, "delphi": 3}

# Method descriptions for the resource
METHOD_INFO = {
    "standard": {
        "name": "Standard",
        "description": "Balanced 5-phase discussion",
        "best_for": "General questions, balanced analysis",
        "phases": ["Answer", "Critique", "Discuss", "Position", "Synthesis"],
    },
    "oxford": {
        "name": "Oxford",
        "description": "Formal debate with FOR/AGAINST teams",
        "best_for": "Controversial topics, policy debates",
        "requires": "Even number of models (2, 4, 6...)",
        "phases": ["Opening", "Rebuttal", "Closing", "Judgement"],
    },
    "advocate": {
        "name": "Advocate",
        "description": "Devil's advocate challenges the group",
        "best_for": "Risk analysis, finding flaws",
        "requires": "3+ models",
        "phases": ["Initial Position", "Cross-Examination", "Verdict"],
    },
    "socratic": {
        "name": "Socratic",
        "description": "Deep inquiry through questioning",
        "best_for": "Deep understanding, exploring fundamentals",
        "phases": ["Thesis", "Inquiry", "Aporia"],
    },
    "delphi": {
        "name": "Delphi",
        "description": "Iterative consensus for estimates",
        "best_for": "Forecasts, time estimates, quantitative predictions",
        "requires": "3+ models",
        "phases": ["Round 1", "Round 2", "Round 3", "Aggregation"],
    },
    "brainstorm": {
        "name": "Brainstorm",
        "description": "Creative ideation",
        "best_for": "Generating ideas, creative solutions",
        "phases": ["Diverge", "Build", "Converge", "Synthesis"],
    },
    "tradeoff": {
        "name": "Tradeoff",
        "description": "Structured comparison of alternatives",
        "best_for": "A vs B decisions, multi-criteria analysis",
        "phases": ["Frame", "Criteria", "Evaluate", "Decide"],
    },
}



def _read_files(file_paths: list[str]) -> tuple[str, list[str]]:
    """Read files and return formatted context string.

    Args:
        file_paths: List of absolute file paths to read.

    Returns:
        Tuple of (context_string, errors).
    """
    if len(file_paths) > MAX_FILES:
        return "", [f"Too many files: {len(file_paths)} > {MAX_FILES}"]

    context_parts = []
    errors = []
    total_size = 0

    for path_str in file_paths:
        try:
            path = Path(path_str)
            if not path.is_absolute():
                errors.append(f"Not absolute path: {path_str}")
                continue

            if not path.exists():
                errors.append(f"File not found: {path_str}")
                continue

            if not path.is_file():
                errors.append(f"Not a file: {path_str}")
                continue

            size = path.stat().st_size
            if size > MAX_FILE_SIZE:
                errors.append(f"File too large ({size} > {MAX_FILE_SIZE}): {path_str}")
                continue

            if total_size + size > MAX_TOTAL_CONTEXT:
                errors.append(f"Total context limit reached, skipping: {path_str}")
                continue

            content = path.read_text(encoding="utf-8", errors="replace")
            total_size += len(content)

            # Format with filename header
            context_parts.append(f"=== {path.name} ===\n{content}")

        except Exception as e:
            errors.append(f"Error reading {path_str}: {e}")

    context = "\n\n".join(context_parts)
    return context, errors




# ─────────────────────────────────────────────────────────────
# Runs
# ─────────────────────────────────────────────────────────────


@dataclass
class Run:
    id: str
    cwd: str
    method: str
    participants: list[str]
    status: str = "running"  # running | done | failed
    phase: str = "starting"
    progress: list[str] = field(default_factory=list)
    messages: list[dict] = field(default_factory=list)
    dropped: dict[str, str] = field(default_factory=dict)
    result: dict | None = None
    error: str | None = None
    started: float = field(default_factory=time.time)
    task: asyncio.Task | None = None


RUNS: dict[str, Run] = {}


def _compact_result(run: Run, s: dict) -> dict[str, Any]:
    return {
        "consensus": s.get("consensus"),
        "synthesis": s.get("synthesis"),
        "differences": s.get("differences"),
        "synthesizer": s.get("synthesizer_model"),
        "positions": [
            {"participant": p["source"], "confidence": p["confidence"], "position": p["position"][:500]}
            for p in s.get("positions") or []
        ],
        "method": run.method,
        "participants": run.participants,
        "dropped": run.dropped,
    }


async def _execute(run: Run, question: str, turn_seconds: float, total_seconds: float) -> None:
    """Run the discussion in this task's own context (cwd, timeouts, drop tracking)."""
    from quorum.team import FourPhaseConsensusTeam

    RUN_CWD.set(run.cwd)
    RUN_FAILED.set(run.dropped)
    TURN_TIMEOUT.set(turn_seconds)
    synthesis: dict | None = None

    async def body() -> None:
        nonlocal synthesis
        team = FourPhaseConsensusTeam(
            model_ids=run.participants,
            method_override=run.method,
            synthesizer_override="first",
            use_language_settings=False,
        )
        async for msg in team.run_stream(question):
            kind = type(msg).__name__
            data = {"type": kind, **(asdict(msg) if is_dataclass(msg) else {"value": str(msg)})}
            run.messages.append(data)
            if kind == "PhaseMarker":
                names = METHOD_INFO.get(run.method, {}).get("phases", [])
                label = names[msg.phase - 1] if 0 < msg.phase <= len(names) else msg.message_key
                run.phase = f"phase {msg.phase}/{msg.total_phases}: {label}"
                run.progress.append(run.phase)
            elif kind == "ThinkingComplete":
                run.progress.append(f"{msg.model} replied")
            elif kind == "SynthesisResult":
                synthesis = data
            if len(run.participants) - len(run.dropped) < 2:
                raise RuntimeError(f"fewer than 2 participants left; dropped: {run.dropped}")

    try:
        await asyncio.wait_for(body(), total_seconds)
        if synthesis is None or str(synthesis.get("synthesis", "")).startswith("[Error"):
            raise RuntimeError(f"no synthesis produced: {(synthesis or {}).get('synthesis')}")
        run.result = _compact_result(run, synthesis)
        run.status = "done"
    except asyncio.TimeoutError:
        run.status, run.error = "failed", f"run exceeded {total_seconds / 60:.0f} minutes"
    except Exception as e:
        run.status, run.error = "failed", str(e)[:1000]
    finally:
        run.phase = run.status
        RUNS_DIR.mkdir(parents=True, exist_ok=True)
        path = RUNS_DIR / f"{run.id}.json"
        path.write_text(json.dumps({"run": _status(run, full=False), "messages": run.messages}, indent=2))
        if run.result is not None:
            run.result["transcript_file"] = str(path)


def _status(run: Run, full: bool) -> dict[str, Any]:
    out: dict[str, Any] = {
        "run_id": run.id,
        "status": run.status,
        "phase": run.phase,
        "elapsed_seconds": round(time.time() - run.started),
        "participants": run.participants,
        "dropped": run.dropped,
        "recent_progress": run.progress[-8:],
    }
    if run.result is not None:
        out["result"] = run.result
    if run.error:
        out["error"] = run.error
    if full:
        out["transcript"] = run.messages
    return out


# ─────────────────────────────────────────────────────────────
# Tool handlers
# ─────────────────────────────────────────────────────────────


async def _list_models(args: dict[str, Any]) -> dict[str, Any]:
    catalog = await discover(refresh=bool(args.get("refresh")))
    return {
        "agents": catalog,
        "presets": {name: resolve_preset(name, catalog) for name in PRESETS},
        "efforts": list(EFFORTS),
        "methods": METHOD_INFO,
        "limits": {
            "max_participants": DEFAULT_MAX_PARTICIPANTS,
            "turn_timeout_minutes": DEFAULT_TURN_MINUTES,
            "total_timeout_minutes": DEFAULT_TOTAL_MINUTES,
        },
    }


async def _start(args: dict[str, Any]) -> dict[str, Any]:
    if os.environ.get("QUORUM_PARTICIPANT"):
        raise ValueError("Nested Quorum runs are not allowed from inside a participant.")

    cwd = str(Path(args.get("cwd") or os.getcwd()).resolve())
    if not Path(cwd).is_dir():
        raise ValueError(f"cwd is not a directory: {cwd}")
    busy = [r.id for r in RUNS.values() if r.cwd == cwd and r.status == "running"]
    if busy:
        raise ValueError(f"A run is already active for {cwd}: {busy[0]}. Wait for it first.")

    method = args.get("method", "standard")
    effort = args.get("effort")
    catalog = await discover()
    ids = args.get("participants") or resolve_preset(args.get("preset", "balanced"), catalog)
    participants = [parse_participant(pid, effort) for pid in ids]

    for p in participants:
        entry = catalog.get(p.agent) or {}
        if entry.get("status") != "ok":
            raise ValueError(f"{p.agent} is unavailable: {entry.get('detail', 'unknown')}")
        known = {m["model"] for m in entry["models"]}
        if p.agent != "claude" and p.model not in known:  # claude also accepts full model ids
            raise ValueError(f"Unknown {p.agent} model '{p.model}'. Known: {', '.join(sorted(known))}")

    max_participants = int(args.get("max_participants", DEFAULT_MAX_PARTICIPANTS))
    pids = list(dict.fromkeys(p.id for p in participants))
    if not 2 <= len(pids) <= max_participants:
        raise ValueError(f"Need 2 to {max_participants} distinct participants, got {len(pids)}: {pids}")
    if len(pids) < METHOD_MIN.get(method, 2):
        raise ValueError(f"Method '{method}' needs at least {METHOD_MIN[method]} participants.")
    if method == "oxford" and len(pids) % 2:
        raise ValueError("Method 'oxford' needs an even number of participants.")

    question = args["question"]
    file_paths = args.get("files") or []
    file_context, file_errors = _read_files(file_paths) if file_paths else ("", [])
    if file_errors:
        raise ValueError("File errors: " + "; ".join(file_errors))
    if file_context:
        question = f"Context files:\n\n{file_context}\n\n---\n\nQuestion: {question}"

    run = Run(id=uuid.uuid4().hex[:12], cwd=cwd, method=method, participants=pids)
    RUNS[run.id] = run
    turn = float(args.get("turn_timeout_minutes", DEFAULT_TURN_MINUTES)) * 60
    total = float(args.get("total_timeout_minutes", DEFAULT_TOTAL_MINUTES)) * 60
    run.task = asyncio.create_task(_execute(run, question, turn, total))
    return {"run_id": run.id, "participants": pids, "method": method, "cwd": cwd,
            "next": f"Call quorum_wait with run_id '{run.id}' until status is not 'running'."}


async def _wait(args: dict[str, Any]) -> dict[str, Any]:
    run = RUNS.get(args["run_id"])
    if run is None:
        raise ValueError(f"Unknown run_id '{args['run_id']}' (runs live only as long as this server).")
    seconds = min(float(args.get("max_seconds", WAIT_DEFAULT_SECONDS)), WAIT_MAX_SECONDS)
    if run.task and not run.task.done():
        await asyncio.wait({run.task}, timeout=seconds)
    return _status(run, full=bool(args.get("full")))


async def _check(args: dict[str, Any]) -> dict[str, Any]:
    catalog = await discover(refresh=True)
    agents = args.get("agents") or list(AGENTS)
    results = await asyncio.gather(*(ping(a, catalog) for a in agents))
    return dict(zip(agents, results))


HANDLERS = {
    "quorum_list_models": _list_models,
    "quorum_start": _start,
    "quorum_wait": _wait,
    "quorum_check": _check,
}


# ─────────────────────────────────────────────────────────────
# MCP wiring
# ─────────────────────────────────────────────────────────────

server = Server("quorum")


@server.list_resources()
async def list_resources() -> list[types.Resource]:
    return [
        types.Resource(
            uri="quorum://methods",
            name="Discussion Methods",
            description="The 7 discussion methods available in Quorum",
            mimeType="application/json",
        ),
    ]


@server.read_resource()
async def read_resource(uri: Any) -> str:
    if str(uri) == "quorum://methods":
        return json.dumps(METHOD_INFO, indent=2)
    raise ValueError(f"Unknown resource: {uri}")


PARTICIPANT_HELP = (
    "Participant ids are 'agent:model@effort', e.g. 'claude:opus@high', 'codex:gpt-6-sol@medium', "
    "'agy:gemini-3.1-pro-high'. The first participant writes the synthesis, so put the strongest first."
)


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="quorum_list_models",
            description=(
                "List the agent CLIs (claude, codex, agy) available as Quorum participants: login status, "
                "current models with descriptions and roles (flagship/workhorse/fast), supported effort "
                "levels, resolved presets, discussion methods and limits. Call this before quorum_start "
                "unless you use a preset. Cached for an hour; pass refresh=true to rediscover."
            ),
            inputSchema={
                "type": "object",
                "properties": {"refresh": {"type": "boolean", "default": False}},
            },
        ),
        types.Tool(
            name="quorum_start",
            description=(
                "Start a Quorum discussion between agent CLIs. Only use when the user asks for one. "
                "Participants can read the project (read-only) and search the web. Returns a run_id "
                "immediately; then call quorum_wait until the status is 'done' or 'failed', and present "
                "the synthesis to the user. " + PARTICIPANT_HELP
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "The question or topic to discuss."},
                    "participants": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Explicit participant ids. Omit to use the preset. " + PARTICIPANT_HELP,
                    },
                    "preset": {
                        "type": "string",
                        "enum": list(PRESETS),
                        "default": "balanced",
                        "description": (
                            "Used when participants is omitted: one participant per available agent. "
                            "quick = fast models/low effort, balanced = workhorse/medium, deep = flagship/high."
                        ),
                    },
                    "effort": {
                        "type": "string",
                        "enum": list(EFFORTS),
                        "description": "Default effort for participants that do not give '@effort'.",
                    },
                    "method": {
                        "type": "string",
                        "enum": list(METHOD_INFO),
                        "default": "standard",
                        "description": "Discussion method; see quorum_list_models for what each is best for.",
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Absolute project directory participants may read. Default: server cwd.",
                    },
                    "files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Absolute file paths to inline as context (max 10, 100KB each).",
                    },
                    "max_participants": {"type": "integer", "default": DEFAULT_MAX_PARTICIPANTS},
                    "turn_timeout_minutes": {"type": "number", "default": DEFAULT_TURN_MINUTES},
                    "total_timeout_minutes": {"type": "number", "default": DEFAULT_TOTAL_MINUTES},
                },
                "required": ["question"],
            },
        ),
        types.Tool(
            name="quorum_wait",
            description=(
                "Wait up to max_seconds for a Quorum run, then return its status, phase, recent progress "
                "and dropped participants; when done, the result (consensus, synthesis, differences, "
                "final positions). Call repeatedly while status is 'running'. full=true adds the whole "
                "transcript — only when the user asks for it."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "run_id": {"type": "string"},
                    "max_seconds": {"type": "number", "default": WAIT_DEFAULT_SECONDS},
                    "full": {"type": "boolean", "default": False},
                },
                "required": ["run_id"],
            },
        ),
        types.Tool(
            name="quorum_check",
            description=(
                "Health check: rediscover the agents and send each a real one-word ping with its fast "
                "model. Uses a little quota; only call when the user asks or a run failed to start."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "agents": {"type": "array", "items": {"type": "string", "enum": list(AGENTS)}},
                },
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    handler = HANDLERS.get(name)
    if handler is None:
        raise ValueError(f"Unknown tool: {name}")
    result = await handler(arguments or {})
    return [types.TextContent(type="text", text=json.dumps(result, indent=2))]


async def _run_server() -> None:
    async with mcp.server.stdio.stdio_server() as (read, write):
        await server.run(
            read,
            write,
            InitializationOptions(
                server_name="quorum",
                server_version=__version__,
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


def main() -> None:
    """Run the Quorum MCP server."""
    asyncio.run(_run_server())
