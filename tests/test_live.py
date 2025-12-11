#!/usr/bin/env python3
"""
Live test script for manually verifying debate flows.
Runs actual debates with visible output.

NOTE: These tests require live API keys and make actual API calls.
They are excluded from CI and should be run manually.

Usage:
    python tests/test_live.py                  # Run all methods
    python tests/test_live.py standard         # Run specific method
    python tests/test_live.py oxford advocate  # Run multiple methods
"""

import asyncio
import sys
from typing import Any

import pytest

# Mark entire module as requiring live API keys
pytestmark = pytest.mark.live

from quorum.team import (
    CritiqueResponse,
    FinalPosition,
    FourPhaseConsensusTeam,
    IndependentAnswer,
    PhaseMarker,
    SynthesisResult,
    TeamTextMessage,
    ThinkingIndicator,
)

# ANSI colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RED = "\033[91m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

# Configure models based on your .env
MODELS_2 = ["claude-sonnet-4-5-20250929", "gemini-2.5-flash"]
MODELS_3 = ["claude-sonnet-4-5-20250929", "gemini-2.5-flash", "grok-4-1-fast-reasoning"]
MODELS_4 = ["claude-sonnet-4-5-20250929", "gemini-2.5-flash", "grok-4-1-fast-reasoning", "gpt-5.1-2025-11-13"]


def truncate(text: str, max_len: int = 300) -> str:
    """Truncate text for display."""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


def print_message(msg: Any) -> None:
    """Pretty print a debate message."""
    if isinstance(msg, ThinkingIndicator):
        print(f"{DIM}  ⏳ {msg.model} is thinking...{RESET}")

    elif isinstance(msg, PhaseMarker):
        print(f"\n{BOLD}{BLUE}{'═'*70}{RESET}")
        print(f"{BOLD}{BLUE}  PHASE {msg.phase}/{msg.total_phases}: {msg.message}{RESET}")
        print(f"{DIM}  Method: {msg.method}, Participants: {msg.num_participants}{RESET}")
        print(f"{BOLD}{BLUE}{'═'*70}{RESET}\n")

    elif isinstance(msg, IndependentAnswer):
        print(f"{GREEN}┌─ {msg.source} (Independent Answer){RESET}")
        print(f"{GREEN}│{RESET} {truncate(msg.content)}")
        print(f"{GREEN}└{'─'*50}{RESET}\n")

    elif isinstance(msg, CritiqueResponse):
        print(f"{YELLOW}┌─ {msg.source} (Critique){RESET}")
        if msg.agreements:
            print(f"{YELLOW}│{RESET} {GREEN}✓ Agreements:{RESET} {truncate(msg.agreements, 100)}")
        if msg.disagreements:
            print(f"{YELLOW}│{RESET} {RED}✗ Disagreements:{RESET} {truncate(msg.disagreements, 100)}")
        if msg.missing:
            print(f"{YELLOW}│{RESET} {CYAN}? Missing:{RESET} {truncate(msg.missing, 100)}")
        print(f"{YELLOW}└{'─'*50}{RESET}\n")

    elif isinstance(msg, TeamTextMessage):
        role_color = {
            "FOR": GREEN,
            "AGAINST": RED,
            "ADVOCATE": RED,
            "DEFENDER": GREEN,
            "QUESTIONER": CYAN,
            "RESPONDENT": YELLOW,
        }.get(msg.role, RESET)

        role_str = f" [{msg.role}]" if msg.role else ""
        round_str = f" ({msg.round_type})" if msg.round_type else ""

        print(f"{role_color}┌─ {msg.source}{role_str}{round_str}{RESET}")
        print(f"{role_color}│{RESET} {truncate(msg.content)}")
        print(f"{role_color}└{'─'*50}{RESET}\n")

    elif isinstance(msg, FinalPosition):
        conf_color = {"HIGH": GREEN, "MEDIUM": YELLOW, "LOW": RED}.get(msg.confidence, RESET)
        print(f"{MAGENTA}┌─ {msg.source} (Final Position) {conf_color}[{msg.confidence}]{RESET}")
        print(f"{MAGENTA}│{RESET} {truncate(msg.position)}")
        print(f"{MAGENTA}└{'─'*50}{RESET}\n")

    elif isinstance(msg, SynthesisResult):
        cons_color = {"YES": GREEN, "PARTIAL": YELLOW, "NO": RED}.get(msg.consensus, RESET)
        print(f"\n{BOLD}{MAGENTA}{'═'*70}{RESET}")
        print(f"{BOLD}{MAGENTA}  SYNTHESIS by {msg.synthesizer_model}{RESET}")
        print(f"{MAGENTA}{'═'*70}{RESET}")
        print(f"{BOLD}  Consensus: {cons_color}{msg.consensus}{RESET}")
        if msg.confidence_breakdown:
            print(f"  Confidence: {GREEN}HIGH={msg.confidence_breakdown.get('HIGH', 0)}{RESET} "
                  f"{YELLOW}MED={msg.confidence_breakdown.get('MEDIUM', 0)}{RESET} "
                  f"{RED}LOW={msg.confidence_breakdown.get('LOW', 0)}{RESET}")
        print(f"\n{BOLD}  Summary:{RESET}")
        print(f"  {truncate(msg.synthesis, 500)}")
        if msg.differences and msg.differences != "None":
            print(f"\n{BOLD}  Differences:{RESET}")
            print(f"  {truncate(msg.differences, 200)}")
        print(f"{MAGENTA}{'═'*70}{RESET}\n")


async def run_debate(method: str, models: list[str], question: str) -> None:
    """Run a complete debate with live output."""
    print(f"\n{BOLD}{CYAN}{'#'*70}{RESET}")
    print(f"{BOLD}{CYAN}  {method.upper()} DEBATE{RESET}")
    print(f"{BOLD}{CYAN}{'#'*70}{RESET}")
    print(f"\n{BOLD}Question:{RESET} {question}")
    print(f"{BOLD}Models:{RESET} {', '.join(models)}")
    print(f"{BOLD}Method:{RESET} {method}\n")

    team = FourPhaseConsensusTeam(
        model_ids=models,
        max_discussion_turns=4,
        method_override=method if method != "standard" else None,
    )

    message_count = 0
    phase_count = 0

    async for msg in team.run_stream(task=question):
        print_message(msg)
        message_count += 1
        if isinstance(msg, PhaseMarker):
            phase_count += 1

    print(f"\n{GREEN}✓ Debate complete!{RESET}")
    print(f"  Phases: {phase_count}, Messages: {message_count}")


async def test_standard():
    """Test Standard flow."""
    await run_debate(
        method="standard",
        models=MODELS_2,
        question="What is the best way to handle errors in Python? Be concise."
    )


async def test_oxford():
    """Test Oxford debate flow."""
    await run_debate(
        method="oxford",
        models=MODELS_2,
        question="Motion: Artificial Intelligence will be net positive for humanity in the next 50 years."
    )


async def test_advocate():
    """Test Devil's Advocate flow."""
    await run_debate(
        method="advocate",
        models=MODELS_3,
        question="What are the best practices for API design? Challenge any consensus."
    )


async def test_socratic():
    """Test Socratic dialogue flow."""
    await run_debate(
        method="socratic",
        models=MODELS_2,
        question="What is knowledge, and how do we know we have it?"
    )


async def test_delphi():
    """Test Delphi consensus flow."""
    await run_debate(
        method="delphi",
        models=MODELS_3,
        question="How long would it take to migrate a 100k LOC Python 2 codebase to Python 3?"
    )


async def test_brainstorm():
    """Test Brainstorm creative ideation flow."""
    await run_debate(
        method="brainstorm",
        models=MODELS_2,
        question="How might we reduce plastic waste in urban areas?"
    )


async def test_tradeoff():
    """Test Tradeoff structured comparison flow."""
    await run_debate(
        method="tradeoff",
        models=MODELS_2,
        question="Should we use PostgreSQL or MongoDB for a new social media app?"
    )


async def main():
    """Main entry point."""
    all_methods = ["standard", "oxford", "advocate", "socratic", "delphi", "brainstorm", "tradeoff"]
    methods = sys.argv[1:] if len(sys.argv) > 1 else all_methods

    for method in methods:
        method = method.lower()
        if method == "standard":
            await test_standard()
        elif method == "oxford":
            await test_oxford()
        elif method == "advocate":
            await test_advocate()
        elif method == "socratic":
            await test_socratic()
        elif method == "delphi":
            await test_delphi()
        elif method == "brainstorm":
            await test_brainstorm()
        elif method == "tradeoff":
            await test_tradeoff()
        else:
            print(f"{RED}Unknown method: {method}{RESET}")
            print(f"Valid methods: {', '.join(all_methods)}")
            sys.exit(1)

        print("\n")


if __name__ == "__main__":
    asyncio.run(main())
