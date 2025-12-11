"""Brainstorm method: Divergent then convergent ideation."""

from __future__ import annotations

import logging
import re
from typing import AsyncIterator

from ..agents import (
    _make_valid_identifier,
    get_brainstorm_build_prompt,
    get_brainstorm_converge_prompt,
    get_brainstorm_diverge_prompt,
    get_brainstorm_synthesis_prompt,
)
from ..models import extract_api_error
from .base import (
    BaseMethodOrchestrator,
    MessageType,
    SynthesisResult,
    ThinkingIndicator,
)

logger = logging.getLogger(__name__)


class BrainstormMethod(BaseMethodOrchestrator):
    """Brainstorm: Divergent idea generation then convergent selection.

    Based on Alex Osborn's methodology (1953, "Applied Imagination").
    Osborn's 4 rules: Defer judgment, wild ideas, quantity, build on others.

    Phase 1: Diverge - Generate wild ideas (no judgment!)
    Phase 2: Build - Combine and expand on each other's ideas
    Phase 3: Converge - Select and refine top ideas
    Phase 4: Synthesis - Compile final selected ideas
    """

    @property
    def method_name(self) -> str:
        return "brainstorm"

    @property
    def total_phases(self) -> int:
        return 4

    async def run_stream(self, task: str) -> AsyncIterator[MessageType]:
        """Run brainstorm ideation flow."""
        self._original_task = task

        # === PHASE 1: Diverge - Generate Wild Ideas ===
        yield self._create_phase_marker(1)

        diverge_ideas = await self._run_brainstorm_diverge(task)

        for model_id in self.model_ids:
            agent_name = _make_valid_identifier(model_id)
            if agent_name in diverge_ideas:
                self._message_count += 1
                yield self._create_team_message(model_id, diverge_ideas[agent_name], "IDEATOR")

        # === PHASE 2: Build - Combine & Expand ===
        yield self._create_phase_marker(2)

        all_ideas_text = self._format_brainstorm_ideas(diverge_ideas)
        build_ideas = await self._run_brainstorm_build(all_ideas_text)

        for model_id in self.model_ids:
            agent_name = _make_valid_identifier(model_id)
            if agent_name in build_ideas:
                self._message_count += 1
                yield self._create_team_message(model_id, build_ideas[agent_name], "IDEATOR")

        # === PHASE 3: Converge - Select & Refine ===
        yield self._create_phase_marker(3)

        all_content = all_ideas_text + "\n\n=== BUILD-ONS ===\n" + self._format_brainstorm_ideas(build_ideas)
        converge_selections = await self._run_brainstorm_converge(all_content)

        for model_id in self.model_ids:
            agent_name = _make_valid_identifier(model_id)
            if agent_name in converge_selections:
                self._message_count += 1
                yield self._create_team_message(model_id, converge_selections[agent_name], "IDEATOR")

        # === PHASE 4: Synthesis - Compile Final Ideas ===
        yield self._create_phase_marker(4)

        yield ThinkingIndicator(model=self._get_synthesizer_model())
        self._synthesis_result = await self._run_brainstorm_synthesis(task, converge_selections)
        yield self._synthesis_result

    async def _run_brainstorm_diverge(self, task: str) -> dict[str, str]:
        """Phase 1: All models generate wild ideas in parallel."""
        num_participants = len(self.model_ids)
        prompt = get_brainstorm_diverge_prompt(num_participants, task)
        return await self._run_parallel_phase(
            prompt_builder=lambda _: prompt,
            user_message=task,
        )

    async def _run_brainstorm_build(self, all_ideas: str) -> dict[str, str]:
        """Phase 2: All models build on ideas in parallel."""
        num_participants = len(self.model_ids)
        prompt = get_brainstorm_build_prompt(num_participants, all_ideas)
        return await self._run_parallel_phase(
            prompt_builder=lambda _: prompt,
            user_message="Build on the most promising ideas.",
        )

    async def _run_brainstorm_converge(self, all_content: str) -> dict[str, str]:
        """Phase 3: All models select top ideas in parallel."""
        num_participants = len(self.model_ids)
        prompt = get_brainstorm_converge_prompt(num_participants, all_content)
        return await self._run_parallel_phase(
            prompt_builder=lambda _: prompt,
            user_message="Select your top 3 ideas.",
        )

    def _format_brainstorm_ideas(self, ideas: dict[str, str]) -> str:
        """Format brainstorm ideas with model attribution."""
        lines = []
        for model_id in self.model_ids:
            agent_name = _make_valid_identifier(model_id)
            if agent_name in ideas:
                lines.append(f"--- {self._display_name(model_id)}'s Ideas ---\n{ideas[agent_name]}\n")
        return "\n".join(lines)

    async def _run_brainstorm_synthesis(
        self, task: str, selections: dict[str, str]
    ) -> SynthesisResult:
        """Synthesize brainstorm results into final selected ideas."""
        synthesizer_model = self._get_synthesizer_model()
        num_participants = len(self.model_ids)

        all_selections = self._format_brainstorm_ideas(selections)

        prompt = get_brainstorm_synthesis_prompt(
            question=task,
            num_participants=num_participants,
            all_selections=all_selections,
        )

        try:
            response = await self._get_model_response(
                synthesizer_model, prompt, "Compile the final selected ideas."
            )
            return self._parse_brainstorm_synthesis(response, synthesizer_model)
        except Exception as e:
            return SynthesisResult(
                consensus="PARTIAL",
                synthesis=f"[Error during synthesis: {extract_api_error(e)}]",
                differences="Unable to determine due to error",
                raw_content=str(e),
                synthesizer_model=synthesizer_model,
                message_count=self._message_count,
                method="brainstorm",
            )

    def _parse_brainstorm_synthesis(self, content: str, synthesizer_model: str) -> SynthesisResult:
        """Parse brainstorm synthesis response."""
        synthesis = content

        ideas_match = re.search(
            r'IDEA 1:(.+?)(?=ALTERNATIVE DIRECTIONS?:|$)',
            content, re.DOTALL | re.IGNORECASE
        )
        if ideas_match:
            synthesis = "IDEA 1:" + ideas_match.group(1).strip()
        else:
            logger.debug(
                "Brainstorm synthesis parsing fallback for %s: no IDEA sections found, using raw content",
                synthesizer_model
            )

        alt_match = re.search(
            r'ALTERNATIVE DIRECTIONS?:\s*(.+?)$',
            content, re.DOTALL | re.IGNORECASE
        )
        differences = alt_match.group(1).strip() if alt_match else "None"

        idea_count = len(re.findall(r'IDEA \d+:', content, re.IGNORECASE))

        return SynthesisResult(
            consensus=f"{idea_count} SELECTED" if idea_count else "PARTIAL",
            synthesis=synthesis,
            differences=differences,
            raw_content=content,
            synthesizer_model=synthesizer_model,
            message_count=self._message_count,
            method="brainstorm",
        )
