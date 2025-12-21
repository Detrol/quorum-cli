"""MCP server for Quorum multi-agent discussions."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

import mcp.server.stdio
import mcp.types as types
from mcp.server.lowlevel import NotificationOptions, Server
from mcp.server.models import InitializationOptions

from quorum.config import get_settings
from quorum.ipc import VALID_METHODS
from quorum.providers import list_all_models_sync
from quorum.team import FourPhaseConsensusTeam

# Limits for file reading
MAX_FILES = 10
MAX_FILE_SIZE = 100_000  # 100KB per file
MAX_TOTAL_CONTEXT = 500_000  # 500KB total

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

server = Server("quorum")


# ─────────────────────────────────────────────────────────────
# Resources
# ─────────────────────────────────────────────────────────────


@server.list_resources()
async def list_resources() -> list[types.Resource]:
    """List available Quorum resources."""
    return [
        types.Resource(
            uri="quorum://models",
            name="Available Models",
            description="AI models configured for Quorum discussions",
            mimeType="application/json",
        ),
        types.Resource(
            uri="quorum://methods",
            name="Discussion Methods",
            description="The 7 discussion methods available in Quorum",
            mimeType="application/json",
        ),
    ]


@server.read_resource()
async def read_resource(uri: str) -> str:
    """Read a Quorum resource."""
    if uri == "quorum://models":
        models = list_all_models_sync()
        return json.dumps(models, indent=2)

    if uri == "quorum://methods":
        return json.dumps(METHOD_INFO, indent=2)

    raise ValueError(f"Unknown resource: {uri}")


# ─────────────────────────────────────────────────────────────
# Tools
# ─────────────────────────────────────────────────────────────


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """List available Quorum tools."""
    return [
        types.Tool(
            name="quorum_discuss",
            description=(
                "Run a multi-model AI discussion using Quorum. "
                "IMPORTANT: Call quorum_list_models first to see available models before starting. "
                "Model requirements: minimum 2 models; Oxford needs even count (2,4,6); "
                "Advocate and Delphi need 3+. See quorum://methods resource for details. "
                "You can include files as context for code review, analysis, or document comparison. "
                "After the discussion completes, present the synthesis to the user."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The question or topic to discuss",
                    },
                    "models": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Model IDs to participate (e.g., ['gpt-4o', 'claude-sonnet'])",
                    },
                    "method": {
                        "type": "string",
                        "enum": list(VALID_METHODS),
                        "default": "standard",
                        "description": "Discussion method to use",
                    },
                    "full_output": {
                        "type": "boolean",
                        "default": False,
                        "description": (
                            "Return full discussion transcript (all phases). "
                            "Only use this if the user explicitly asks for the full discussion. "
                            "Default: false (returns only the final synthesis, which is usually sufficient)."
                        ),
                    },
                    "files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Absolute file paths to include as context for the discussion. "
                            "Use this for code review, comparing implementations, analyzing documents, "
                            "or any task where models need to see file contents. "
                            "Limits: max 10 files, 100KB each, 500KB total. "
                            "Files are prepended to the question so all models can reference them."
                        ),
                    },
                },
                "required": ["question", "models"],
            },
        ),
        types.Tool(
            name="quorum_list_models",
            description=(
                "List all available AI models configured for Quorum. "
                "ALWAYS call this before quorum_discuss to see which models are available. "
                "Returns models grouped by provider (OpenAI, Anthropic, Google, xAI, Ollama, etc). "
                "Use the model IDs from this list when calling quorum_discuss."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    """Handle tool calls."""
    if name == "quorum_list_models":
        return await _handle_list_models()

    if name == "quorum_discuss":
        return await _handle_discuss(arguments)

    raise ValueError(f"Unknown tool: {name}")


async def _handle_list_models() -> list[types.TextContent]:
    """List all available models."""
    from dataclasses import asdict

    models = list_all_models_sync()
    # Convert ModelInfo dataclasses to dicts for JSON serialization
    serializable = {
        provider: [asdict(m) for m in model_list]
        for provider, model_list in models.items()
    }
    return [types.TextContent(type="text", text=json.dumps(serializable, indent=2))]


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


async def _handle_discuss(args: dict[str, Any]) -> list[types.TextContent]:
    """Run a Quorum discussion."""
    question = args["question"]
    model_ids = args["models"]
    method = args.get("method", "standard")
    full_output = args.get("full_output", False)
    file_paths = args.get("files", [])

    # Read files if provided
    file_context = ""
    file_errors: list[str] = []
    if file_paths:
        file_context, file_errors = _read_files(file_paths)

    # Build full question with file context
    if file_context:
        full_question = f"Context files:\n\n{file_context}\n\n---\n\nQuestion: {question}"
    else:
        full_question = question

    # Initialize before try block so they're available in except
    synthesis = None
    all_messages: list[dict] = []

    try:
        team = FourPhaseConsensusTeam(
            model_ids=model_ids,
            method_override=method,
        )

        async for msg in team.run_stream(full_question):
            if hasattr(msg, "__dict__"):
                msg_dict = {
                    "type": type(msg).__name__,
                    **msg.__dict__,
                }
                all_messages.append(msg_dict)

                # Capture synthesis for compact output
                if type(msg).__name__ == "SynthesisResult":
                    synthesis = msg_dict

        # Return full output or just synthesis
        if full_output:
            return [types.TextContent(type="text", text=json.dumps(all_messages, indent=2))]

        # Compact: return only synthesis
        if synthesis:
            # Clean up synthesis for readability
            compact_result: dict[str, Any] = {
                "consensus": synthesis.get("consensus"),
                "synthesis": synthesis.get("synthesis"),
                "differences": synthesis.get("differences"),
                "method": synthesis.get("method"),
                "models": model_ids,
            }
            if file_errors:
                compact_result["file_errors"] = file_errors
            if file_paths:
                compact_result["files_included"] = len(file_paths) - len(file_errors)
            return [types.TextContent(type="text", text=json.dumps(compact_result, indent=2))]

        # Fallback if no synthesis (shouldn't happen)
        return [types.TextContent(type="text", text=json.dumps(all_messages, indent=2))]

    except ValueError as e:
        # Configuration errors (invalid model, missing API key, etc.)
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "error_type": "configuration",
                "models": model_ids,
                "method": method,
            }),
        )]

    except Exception as e:
        # Unexpected errors during discussion
        error_msg = str(e)
        # Truncate very long error messages
        if len(error_msg) > 500:
            error_msg = error_msg[:500] + "..."

        return [types.TextContent(
            type="text",
            text=json.dumps({
                "error": error_msg,
                "error_type": "discussion_failed",
                "models": model_ids,
                "method": method,
                "partial_results": len(all_messages),
            }),
        )]


# ─────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────


async def _run_server() -> None:
    """Run the MCP server with stdio transport."""
    async with mcp.server.stdio.stdio_server() as (read, write):
        await server.run(
            read,
            write,
            InitializationOptions(
                server_name="quorum",
                server_version="1.1.2",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


def main() -> None:
    """Run the Quorum MCP server."""
    # Verify config exists
    settings = get_settings()
    if not settings.available_providers:
        print(
            "No providers configured. Run 'quorum' first to configure.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Run server
    asyncio.run(_run_server())


if __name__ == "__main__":
    main()
