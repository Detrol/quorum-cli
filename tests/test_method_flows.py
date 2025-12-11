"""
Integration tests for all debate method flows.
Verifies authentic structure and phase progression.

NOTE: These tests make real API calls and can be slow/expensive.
They are excluded from CI and require API keys to run.

Run selectively with: pytest tests/test_method_flows.py -v -k "test_name" -m live

Quick smoke test (one method):
    pytest tests/test_method_flows.py::TestStandardFlow::test_phase_structure -v -m live

Full test suite:
    pytest tests/test_method_flows.py -v -m live
"""

from dataclasses import dataclass
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

# Use models that are configured in .env
# Adjust these based on your configuration
MODELS_2 = ["claude-sonnet-4-5-20250929", "gemini-2.5-flash"]
MODELS_3 = ["claude-sonnet-4-5-20250929", "gemini-2.5-flash", "grok-4-1-fast-reasoning"]
MODELS_4 = ["claude-sonnet-4-5-20250929", "gemini-2.5-flash", "grok-4-1-fast-reasoning", "gpt-5.1-2025-11-13"]


@dataclass
class FlowRecording:
    """Records all messages from a debate flow."""
    phases: list[PhaseMarker]
    messages: list[Any]

    @property
    def phase_count(self) -> int:
        return len(self.phases)

    def messages_in_phase(self, phase: int) -> list[Any]:
        """Get messages between phase markers."""
        start_idx = None
        end_idx = len(self.messages)

        for i, msg in enumerate(self.messages):
            if isinstance(msg, PhaseMarker):
                if msg.phase == phase:
                    start_idx = i + 1
                elif msg.phase == phase + 1:
                    end_idx = i
                    break

        if start_idx is None:
            return []
        return self.messages[start_idx:end_idx]

    def print_summary(self):
        """Print a summary of the recording for debugging."""
        print(f"\n{'='*60}")
        print(f"Total phases: {self.phase_count}")
        print(f"Total messages: {len(self.messages)}")
        for phase in self.phases:
            print(f"  Phase {phase.phase}: {phase.message[:50]}... (method={phase.method}, total={phase.total_phases})")
        print(f"{'='*60}\n")


async def run_and_record(
    model_ids: list[str],
    question: str,
    method: str,
    role_assignments: dict | None = None,
    max_turns: int = 4,
) -> FlowRecording:
    """Run a debate and record all messages."""
    team = FourPhaseConsensusTeam(
        model_ids=model_ids,
        max_discussion_turns=max_turns,
        method_override=method if method != "standard" else None,
        role_assignments=role_assignments,
    )

    phases = []
    messages = []

    async for msg in team.run_stream(task=question):
        if isinstance(msg, ThinkingIndicator):
            continue  # Skip thinking indicators

        messages.append(msg)
        if isinstance(msg, PhaseMarker):
            phases.append(msg)

    return FlowRecording(phases=phases, messages=messages)


class TestStandardFlow:
    """Test standard 5-phase consensus flow."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(300)  # 5 min timeout
    async def test_phase_structure(self):
        """Verify standard flow has 5 phases with correct metadata."""
        recording = await run_and_record(
            MODELS_2,
            "What is 2+2? Give a brief answer.",
            "standard"
        )

        recording.print_summary()

        # Verify 5 phases
        assert recording.phase_count == 5, f"Expected 5 phases, got {recording.phase_count}"

        # Verify phase metadata
        for phase in recording.phases:
            assert phase.method == "standard", f"Phase {phase.phase} has method={phase.method}"
            assert phase.total_phases == 5, f"Phase {phase.phase} has total_phases={phase.total_phases}"

        # Verify phase numbers are sequential
        phase_nums = [p.phase for p in recording.phases]
        assert phase_nums == [1, 2, 3, 4, 5], f"Phase numbers: {phase_nums}"

    @pytest.mark.asyncio
    @pytest.mark.timeout(300)
    async def test_phase1_independent_answers(self):
        """Verify Phase 1 produces IndependentAnswer from each model."""
        recording = await run_and_record(MODELS_2, "What is 1+1?", "standard")

        phase1_msgs = recording.messages_in_phase(1)
        answers = [m for m in phase1_msgs if isinstance(m, IndependentAnswer)]

        # Each model should have one answer
        assert len(answers) == len(MODELS_2), f"Expected {len(MODELS_2)} answers, got {len(answers)}"
        sources = {a.source for a in answers}
        assert sources == set(MODELS_2), f"Sources: {sources}, expected: {set(MODELS_2)}"

    @pytest.mark.asyncio
    @pytest.mark.timeout(300)
    async def test_phase2_critiques(self):
        """Verify Phase 2 produces CritiqueResponse from each model."""
        recording = await run_and_record(MODELS_2, "What is 1+1?", "standard")

        phase2_msgs = recording.messages_in_phase(2)
        critiques = [m for m in phase2_msgs if isinstance(m, CritiqueResponse)]

        # Each model should have one critique
        assert len(critiques) == len(MODELS_2), f"Expected {len(MODELS_2)} critiques, got {len(critiques)}"

    @pytest.mark.asyncio
    @pytest.mark.timeout(300)
    async def test_phase4_final_positions(self):
        """Verify Phase 4 produces FinalPosition with valid confidence."""
        recording = await run_and_record(MODELS_2, "What is 1+1?", "standard")

        phase4_msgs = recording.messages_in_phase(4)
        positions = [m for m in phase4_msgs if isinstance(m, FinalPosition)]

        # Each model should have final position
        assert len(positions) == len(MODELS_2), f"Expected {len(MODELS_2)} positions, got {len(positions)}"

        for pos in positions:
            assert pos.confidence in ("HIGH", "MEDIUM", "LOW"), f"Invalid confidence: {pos.confidence}"

    @pytest.mark.asyncio
    @pytest.mark.timeout(300)
    async def test_phase5_synthesis(self):
        """Verify Phase 5 produces SynthesisResult with valid consensus."""
        recording = await run_and_record(MODELS_2, "What is 1+1?", "standard")

        synthesis = [m for m in recording.messages if isinstance(m, SynthesisResult)]
        assert len(synthesis) == 1, f"Expected 1 synthesis, got {len(synthesis)}"
        assert synthesis[0].consensus in ("YES", "PARTIAL", "NO"), f"Invalid consensus: {synthesis[0].consensus}"


class TestOxfordFlow:
    """Test Oxford 4-phase debate flow."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(300)
    async def test_phase_structure(self):
        """Verify Oxford flow has 4 phases with correct metadata."""
        # Oxford requires even number of models
        recording = await run_and_record(
            MODELS_2,
            "Motion: AI is beneficial for society. Brief arguments only.",
            "oxford"
        )

        recording.print_summary()

        # Verify 4 phases
        assert recording.phase_count == 4, f"Expected 4 phases, got {recording.phase_count}"

        # Verify phase metadata
        for phase in recording.phases:
            assert phase.method == "oxford", f"Phase {phase.phase} has method={phase.method}"
            assert phase.total_phases == 4, f"Phase {phase.phase} has total_phases={phase.total_phases}"

    @pytest.mark.asyncio
    @pytest.mark.timeout(300)
    async def test_roles_present(self):
        """Verify FOR and AGAINST roles are present."""
        recording = await run_and_record(MODELS_2, "Motion: Cats are better than dogs.", "oxford")

        all_chat_msgs = [m for m in recording.messages if isinstance(m, TeamTextMessage)]
        roles = {m.role for m in all_chat_msgs}

        assert "FOR" in roles, "Missing FOR role"
        assert "AGAINST" in roles, "Missing AGAINST role"

    @pytest.mark.asyncio
    @pytest.mark.timeout(300)
    async def test_round_types(self):
        """Verify correct round_type progression: opening → rebuttal → closing."""
        recording = await run_and_record(MODELS_2, "Motion: Test debate.", "oxford")

        # Phase 1: opening
        phase1_msgs = [m for m in recording.messages_in_phase(1) if isinstance(m, TeamTextMessage)]
        if phase1_msgs:
            assert all(m.round_type == "opening" for m in phase1_msgs), \
                f"Phase 1 round_types: {[m.round_type for m in phase1_msgs]}"

        # Phase 2: rebuttal
        phase2_msgs = [m for m in recording.messages_in_phase(2) if isinstance(m, TeamTextMessage)]
        if phase2_msgs:
            assert all(m.round_type == "rebuttal" for m in phase2_msgs), \
                f"Phase 2 round_types: {[m.round_type for m in phase2_msgs]}"

        # Phase 3: closing
        phase3_msgs = [m for m in recording.messages_in_phase(3) if isinstance(m, TeamTextMessage)]
        if phase3_msgs:
            assert all(m.round_type == "closing" for m in phase3_msgs), \
                f"Phase 3 round_types: {[m.round_type for m in phase3_msgs]}"
            # Only one speaker per side for closing
            assert len(phase3_msgs) == 2, f"Expected 2 closing statements, got {len(phase3_msgs)}"

    @pytest.mark.asyncio
    @pytest.mark.timeout(300)
    async def test_judgement(self):
        """Verify Phase 4 produces a judgement (SynthesisResult)."""
        recording = await run_and_record(MODELS_2, "Motion: Test.", "oxford")

        synthesis = [m for m in recording.messages if isinstance(m, SynthesisResult)]
        assert len(synthesis) == 1, f"Expected 1 judgement, got {len(synthesis)}"


class TestAdvocateFlow:
    """Test Devil's Advocate 3-phase flow."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(300)
    async def test_phase_structure(self):
        """Verify Advocate flow has 3 phases with correct metadata."""
        # Advocate requires at least 3 models
        recording = await run_and_record(
            MODELS_3,
            "What is the best programming language? Brief answers.",
            "advocate"
        )

        recording.print_summary()

        # Verify 3 phases
        assert recording.phase_count == 3, f"Expected 3 phases, got {recording.phase_count}"

        for phase in recording.phases:
            assert phase.method == "advocate", f"Phase {phase.phase} has method={phase.method}"
            assert phase.total_phases == 3, f"Phase {phase.phase} has total_phases={phase.total_phases}"

    @pytest.mark.asyncio
    @pytest.mark.timeout(300)
    async def test_phase1_defenders_only(self):
        """Verify Phase 1 has only DEFENDER messages (advocate doesn't speak)."""
        recording = await run_and_record(MODELS_3, "Best practice?", "advocate")

        phase1_msgs = [m for m in recording.messages_in_phase(1) if isinstance(m, TeamTextMessage)]

        # All should be defenders
        assert all(m.role == "DEFENDER" for m in phase1_msgs), \
            f"Phase 1 roles: {[m.role for m in phase1_msgs]}"

        # Advocate (last model) should not speak in phase 1
        assert len(phase1_msgs) == len(MODELS_3) - 1, \
            f"Expected {len(MODELS_3) - 1} defender messages, got {len(phase1_msgs)}"

    @pytest.mark.asyncio
    @pytest.mark.timeout(300)
    async def test_roles_present(self):
        """Verify both ADVOCATE and DEFENDER roles appear."""
        recording = await run_and_record(MODELS_3, "Best practice?", "advocate")

        all_chat_msgs = [m for m in recording.messages if isinstance(m, TeamTextMessage)]
        roles = {m.role for m in all_chat_msgs}

        assert "ADVOCATE" in roles, "Missing ADVOCATE role"
        assert "DEFENDER" in roles, "Missing DEFENDER role"

    @pytest.mark.asyncio
    @pytest.mark.timeout(300)
    async def test_advocate_is_last_model(self):
        """Verify the advocate is the last model in the list."""
        recording = await run_and_record(MODELS_3, "Best practice?", "advocate")

        advocate_msgs = [m for m in recording.messages
                        if isinstance(m, TeamTextMessage) and m.role == "ADVOCATE"]

        # All advocate messages should be from the last model
        assert all(m.source == MODELS_3[-1] for m in advocate_msgs), \
            f"Advocate sources: {[m.source for m in advocate_msgs]}, expected: {MODELS_3[-1]}"


class TestSocraticFlow:
    """Test Socratic 3-phase dialogue flow."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(300)
    async def test_phase_structure(self):
        """Verify Socratic flow has 3 phases with correct metadata."""
        recording = await run_and_record(
            MODELS_2,
            "What is truth? Brief philosophical answer.",
            "socratic"
        )

        recording.print_summary()

        # Verify 3 phases
        assert recording.phase_count == 3, f"Expected 3 phases, got {recording.phase_count}"

        for phase in recording.phases:
            assert phase.method == "socratic", f"Phase {phase.phase} has method={phase.method}"
            assert phase.total_phases == 3, f"Phase {phase.phase} has total_phases={phase.total_phases}"

    @pytest.mark.asyncio
    @pytest.mark.timeout(300)
    async def test_initial_thesis(self):
        """Verify Phase 1 has single thesis from first model."""
        recording = await run_and_record(MODELS_2, "What is truth?", "socratic")

        phase1_msgs = [m for m in recording.messages_in_phase(1) if isinstance(m, TeamTextMessage)]

        # Only one message (initial thesis)
        assert len(phase1_msgs) == 1, f"Expected 1 thesis, got {len(phase1_msgs)}"
        assert phase1_msgs[0].role == "RESPONDENT", f"Thesis role: {phase1_msgs[0].role}"
        assert phase1_msgs[0].source == MODELS_2[0], f"Thesis from: {phase1_msgs[0].source}"

    @pytest.mark.asyncio
    @pytest.mark.timeout(300)
    async def test_inquiry_roles(self):
        """Verify Phase 2 has QUESTIONER and RESPONDENT alternation."""
        recording = await run_and_record(MODELS_2, "What is truth?", "socratic")

        phase2_msgs = [m for m in recording.messages_in_phase(2) if isinstance(m, TeamTextMessage)]

        # Should alternate QUESTIONER/RESPONDENT
        for i, msg in enumerate(phase2_msgs):
            expected_role = "QUESTIONER" if i % 2 == 0 else "RESPONDENT"
            assert msg.role == expected_role, \
                f"Message {i} has role {msg.role}, expected {expected_role}"

    @pytest.mark.asyncio
    @pytest.mark.timeout(300)
    async def test_insights_phase(self):
        """Verify Phase 3 insights have no role (reflection)."""
        recording = await run_and_record(MODELS_2, "What is truth?", "socratic")

        phase3_msgs = [m for m in recording.messages_in_phase(3) if isinstance(m, TeamTextMessage)]

        # All models should contribute insights with no role
        assert len(phase3_msgs) == len(MODELS_2), \
            f"Expected {len(MODELS_2)} insights, got {len(phase3_msgs)}"
        assert all(m.role is None for m in phase3_msgs), \
            f"Insight roles: {[m.role for m in phase3_msgs]}"


class TestDelphiFlow:
    """Test Delphi iterative consensus flow."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(300)
    async def test_phase_structure(self):
        """Verify Delphi flow has 4 phases with correct metadata."""
        # Delphi requires at least 3 models
        recording = await run_and_record(
            MODELS_3,
            "How long to rewrite 10k lines of code? Give estimate.",
            "delphi"
        )

        recording.print_summary()

        # Verify 4 phases (Round1 → Round2 → Round3 → Aggregation)
        assert recording.phase_count == 4, f"Expected 4 phases, got {recording.phase_count}"

        for phase in recording.phases:
            assert phase.method == "delphi", f"Phase {phase.phase} has method={phase.method}"
            assert phase.total_phases == 4, f"Phase {phase.phase} has total_phases={phase.total_phases}"

    @pytest.mark.asyncio
    @pytest.mark.timeout(300)
    async def test_phase1_estimates(self):
        """Verify Phase 1 has estimates from all panelists."""
        recording = await run_and_record(MODELS_3, "How many days?", "delphi")

        phase1_msgs = [m for m in recording.messages_in_phase(1) if isinstance(m, TeamTextMessage)]

        # All models participate as PANELIST
        assert len(phase1_msgs) == len(MODELS_3), \
            f"Expected {len(MODELS_3)} estimates, got {len(phase1_msgs)}"
        assert all(m.role == "PANELIST" for m in phase1_msgs), \
            f"Roles: {[m.role for m in phase1_msgs]}"

    @pytest.mark.asyncio
    @pytest.mark.timeout(300)
    async def test_synthesis_aggregation(self):
        """Verify final phase produces aggregated estimate."""
        recording = await run_and_record(MODELS_3, "How many hours?", "delphi")

        synthesis = [m for m in recording.messages if isinstance(m, SynthesisResult)]
        assert len(synthesis) == 1, f"Expected 1 synthesis, got {len(synthesis)}"


class TestBrainstormFlow:
    """Test Brainstorm creative ideation flow."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(300)
    async def test_phase_structure(self):
        """Verify Brainstorm flow has 4 phases with correct metadata."""
        recording = await run_and_record(
            MODELS_2,
            "Ideas for reducing traffic? Quick list.",
            "brainstorm"
        )

        recording.print_summary()

        # Verify 4 phases (Diverge → Build → Converge → Synthesis)
        assert recording.phase_count == 4, f"Expected 4 phases, got {recording.phase_count}"

        for phase in recording.phases:
            assert phase.method == "brainstorm", f"Phase {phase.phase} has method={phase.method}"
            assert phase.total_phases == 4, f"Phase {phase.phase} has total_phases={phase.total_phases}"

    @pytest.mark.asyncio
    @pytest.mark.timeout(300)
    async def test_phase1_diverge(self):
        """Verify Phase 1 (Diverge) has ideas from all ideators."""
        recording = await run_and_record(MODELS_2, "Ideas?", "brainstorm")

        phase1_msgs = [m for m in recording.messages_in_phase(1) if isinstance(m, TeamTextMessage)]

        # All models participate as IDEATOR
        assert len(phase1_msgs) == len(MODELS_2), \
            f"Expected {len(MODELS_2)} idea sets, got {len(phase1_msgs)}"
        assert all(m.role == "IDEATOR" for m in phase1_msgs), \
            f"Roles: {[m.role for m in phase1_msgs]}"

    @pytest.mark.asyncio
    @pytest.mark.timeout(300)
    async def test_synthesis_selected_ideas(self):
        """Verify final phase produces selected ideas."""
        recording = await run_and_record(MODELS_2, "Ideas?", "brainstorm")

        synthesis = [m for m in recording.messages if isinstance(m, SynthesisResult)]
        assert len(synthesis) == 1, f"Expected 1 synthesis, got {len(synthesis)}"


class TestTradeoffFlow:
    """Test Tradeoff structured comparison flow."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(300)
    async def test_phase_structure(self):
        """Verify Tradeoff flow has 4 phases with correct metadata."""
        recording = await run_and_record(
            MODELS_2,
            "SQL vs NoSQL for blog? Brief comparison.",
            "tradeoff"
        )

        recording.print_summary()

        # Verify 4 phases (Frame → Criteria → Evaluate → Decide)
        assert recording.phase_count == 4, f"Expected 4 phases, got {recording.phase_count}"

        for phase in recording.phases:
            assert phase.method == "tradeoff", f"Phase {phase.phase} has method={phase.method}"
            assert phase.total_phases == 4, f"Phase {phase.phase} has total_phases={phase.total_phases}"

    @pytest.mark.asyncio
    @pytest.mark.timeout(300)
    async def test_phase1_alternatives(self):
        """Verify Phase 1 (Frame) defines alternatives."""
        recording = await run_and_record(MODELS_2, "A vs B?", "tradeoff")

        phase1_msgs = [m for m in recording.messages_in_phase(1) if isinstance(m, TeamTextMessage)]

        # All models participate as EVALUATOR
        assert len(phase1_msgs) == len(MODELS_2), \
            f"Expected {len(MODELS_2)} framings, got {len(phase1_msgs)}"
        assert all(m.role == "EVALUATOR" for m in phase1_msgs), \
            f"Roles: {[m.role for m in phase1_msgs]}"

    @pytest.mark.asyncio
    @pytest.mark.timeout(300)
    async def test_synthesis_recommendation(self):
        """Verify final phase produces recommendation."""
        recording = await run_and_record(MODELS_2, "X vs Y?", "tradeoff")

        synthesis = [m for m in recording.messages if isinstance(m, SynthesisResult)]
        assert len(synthesis) == 1, f"Expected 1 synthesis, got {len(synthesis)}"


# Quick verification tests - faster, less thorough
class TestQuickVerification:
    """Quick smoke tests to verify basic functionality."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(180)
    async def test_all_methods_run(self):
        """Verify all methods can start and produce output."""
        for method, models, expected_phases in [
            ("standard", MODELS_2, 5),
            ("oxford", MODELS_2, 4),
            ("advocate", MODELS_3, 3),
            ("socratic", MODELS_2, 3),
            ("delphi", MODELS_3, 4),
            ("brainstorm", MODELS_2, 4),
            ("tradeoff", MODELS_2, 4),
        ]:
            print(f"\nTesting {method}...")

            team = FourPhaseConsensusTeam(
                model_ids=models,
                max_discussion_turns=2,
                method_override=method if method != "standard" else None,
            )

            phase_count = 0
            message_count = 0

            async for msg in team.run_stream(task="Quick test."):
                if isinstance(msg, PhaseMarker):
                    phase_count += 1
                    assert msg.method == method, f"{method}: wrong method in PhaseMarker"
                    assert msg.total_phases == expected_phases, f"{method}: wrong total_phases"
                message_count += 1

            assert phase_count == expected_phases, f"{method}: expected {expected_phases} phases, got {phase_count}"
            assert message_count > phase_count, f"{method}: no content messages"
            print(f"  ✓ {method}: {phase_count} phases, {message_count} messages")
