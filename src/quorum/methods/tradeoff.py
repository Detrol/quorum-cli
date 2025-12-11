"""Tradeoff method: Multi-Criteria Decision Analysis (MCDA)."""

from __future__ import annotations

import logging
import re
from typing import AsyncIterator

from ..agents import (
    _make_valid_identifier,
    get_tradeoff_criteria_prompt,
    get_tradeoff_decide_prompt,
    get_tradeoff_evaluate_prompt,
    get_tradeoff_frame_prompt,
)
from ..models import extract_api_error
from .base import (
    BaseMethodOrchestrator,
    MessageType,
    SynthesisResult,
    ThinkingIndicator,
)

logger = logging.getLogger(__name__)


class TradeoffMethod(BaseMethodOrchestrator):
    """Tradeoff: Structured multi-criteria decision analysis.

    Based on MCDA (Multi-Criteria Decision Analysis).
    Key concept: Neutral evaluators score alternatives against criteria.

    Phase 1: Frame - Define alternatives to compare
    Phase 2: Criteria - Establish evaluation dimensions
    Phase 3: Evaluate - Score each option objectively
    Phase 4: Decide - Synthesize recommendation with tradeoff analysis
    """

    @property
    def method_name(self) -> str:
        return "tradeoff"

    @property
    def total_phases(self) -> int:
        return 4

    async def run_stream(self, task: str) -> AsyncIterator[MessageType]:
        """Run tradeoff decision analysis flow."""
        self._original_task = task

        # === PHASE 1: Frame - Define Alternatives ===
        yield self._create_phase_marker(1)

        frame_responses = await self._run_tradeoff_frame(task)

        for model_id in self.model_ids:
            agent_name = _make_valid_identifier(model_id)
            if agent_name in frame_responses:
                self._message_count += 1
                yield self._create_team_message(model_id, frame_responses[agent_name], "EVALUATOR")

        alternatives = self._synthesize_alternatives(frame_responses)

        # === PHASE 2: Criteria - Establish Dimensions ===
        yield self._create_phase_marker(2)

        criteria_responses = await self._run_tradeoff_criteria(alternatives)

        for model_id in self.model_ids:
            agent_name = _make_valid_identifier(model_id)
            if agent_name in criteria_responses:
                self._message_count += 1
                yield self._create_team_message(model_id, criteria_responses[agent_name], "EVALUATOR")

        criteria = self._synthesize_criteria(criteria_responses)
        alternative_names = self._extract_alternative_names(alternatives)

        # === PHASE 3: Evaluate - Score Each Option ===
        yield self._create_phase_marker(3)

        evaluate_responses = await self._run_tradeoff_evaluate(
            alternatives, criteria, alternative_names
        )

        for model_id in self.model_ids:
            agent_name = _make_valid_identifier(model_id)
            if agent_name in evaluate_responses:
                self._message_count += 1
                yield self._create_team_message(model_id, evaluate_responses[agent_name], "EVALUATOR")

        # === PHASE 4: Decide - Synthesize Recommendation ===
        yield self._create_phase_marker(4)

        yield ThinkingIndicator(model=self._get_synthesizer_model())
        self._synthesis_result = await self._run_tradeoff_decide(
            task, alternatives, criteria, evaluate_responses
        )
        yield self._synthesis_result

    async def _run_tradeoff_frame(self, task: str) -> dict[str, str]:
        """Phase 1: All models define alternatives in parallel."""
        num_participants = len(self.model_ids)
        prompt = get_tradeoff_frame_prompt(num_participants, task)
        return await self._run_parallel_phase(
            prompt_builder=lambda _: prompt,
            user_message=task,
        )

    async def _run_tradeoff_criteria(self, alternatives: str) -> dict[str, str]:
        """Phase 2: All models define criteria in parallel."""
        num_participants = len(self.model_ids)
        prompt = get_tradeoff_criteria_prompt(num_participants, alternatives)
        return await self._run_parallel_phase(
            prompt_builder=lambda _: prompt,
            user_message="Define evaluation criteria.",
        )

    async def _run_tradeoff_evaluate(
        self, alternatives: str, criteria: str, alternative_names: list[str]
    ) -> dict[str, str]:
        """Phase 3: All models evaluate alternatives in parallel."""
        num_participants = len(self.model_ids)
        prompt = get_tradeoff_evaluate_prompt(
            num_participants, alternatives, criteria, alternative_names
        )
        return await self._run_parallel_phase(
            prompt_builder=lambda _: prompt,
            user_message="Score each alternative.",
        )

    def _synthesize_alternatives(self, responses: dict[str, str]) -> str:
        """Use first model's alternatives as the framework."""
        return next(iter(responses.values()), "")

    def _synthesize_criteria(self, responses: dict[str, str]) -> str:
        """Use first model's criteria as the framework."""
        return next(iter(responses.values()), "")

    def _extract_alternative_names(self, alternatives: str) -> list[str]:
        """Extract alternative names from the alternatives text."""
        names = []

        matches = re.findall(r'ALTERNATIVE\s+[A-Z]:\s*([^\n]+)', alternatives, re.IGNORECASE)
        for match in matches:
            name = match.strip()
            if name and name.lower() not in ["name", "[name]"]:
                names.append(name)

        seen = set()
        unique_names = []
        for name in names:
            if name.lower() not in seen:
                seen.add(name.lower())
                unique_names.append(name)

        if not unique_names:
            unique_names = ["Alternative A", "Alternative B", "Alternative C"]

        return unique_names[:4]

    def _format_evaluations(self, evaluations: dict[str, str]) -> str:
        """Format evaluations with model attribution."""
        lines = []
        for model_id in self.model_ids:
            agent_name = _make_valid_identifier(model_id)
            if agent_name in evaluations:
                lines.append(f"--- {self._display_name(model_id)}'s Evaluation ---\n{evaluations[agent_name]}\n")
        return "\n".join(lines)

    async def _run_tradeoff_decide(
        self,
        task: str,
        alternatives: str,
        criteria: str,
        evaluations: dict[str, str],
    ) -> SynthesisResult:
        """Synthesize tradeoff results into recommendation."""
        synthesizer_model = self._get_synthesizer_model()
        num_participants = len(self.model_ids)

        all_evaluations = self._format_evaluations(evaluations)

        prompt = get_tradeoff_decide_prompt(
            question=task,
            num_participants=num_participants,
            alternatives=alternatives,
            criteria=criteria,
            all_evaluations=all_evaluations,
        )

        try:
            response = await self._get_model_response(
                synthesizer_model, prompt, "Produce the recommendation."
            )
            return self._parse_tradeoff_synthesis(response, synthesizer_model)
        except Exception as e:
            return SynthesisResult(
                consensus="NO",
                synthesis=f"[Error during decision: {extract_api_error(e)}]",
                differences="Unable to determine due to error",
                raw_content=str(e),
                synthesizer_model=synthesizer_model,
                message_count=self._message_count,
                method="tradeoff",
            )

    def _parse_tradeoff_synthesis(self, content: str, synthesizer_model: str) -> SynthesisResult:
        """Parse tradeoff synthesis response."""
        consensus = "NO"

        agree_match = re.search(r'AGREEMENT:\s*(YES|NO)', content, re.IGNORECASE)
        if agree_match:
            consensus = agree_match.group(1).upper()

        rec_match = re.search(
            r'RECOMMENDATION:\s*(.+?)(?=AGGREGATED|KEY TRADEOFFS?|ANALYSIS|$)',
            content, re.DOTALL | re.IGNORECASE
        )
        recommendation = rec_match.group(1).strip() if rec_match else ""

        analysis_match = re.search(
            r'ANALYSIS:\s*(.+?)(?=WHEN TO CHOOSE|$)',
            content, re.DOTALL | re.IGNORECASE
        )
        if analysis_match:
            synthesis = analysis_match.group(1).strip()
        else:
            logger.debug(
                "Tradeoff synthesis parsing fallback for %s: no ANALYSIS section found, using raw content",
                synthesizer_model
            )
            synthesis = content

        if recommendation:
            synthesis = f"RECOMMENDATION: {recommendation}\n\n{synthesis}"

        tradeoff_match = re.search(
            r'KEY TRADEOFFS?:\s*(.+?)(?=ANALYSIS:|RECOMMENDATION:|WHEN TO CHOOSE|$)',
            content, re.DOTALL | re.IGNORECASE
        )
        differences = tradeoff_match.group(1).strip() if tradeoff_match else "See analysis"

        return SynthesisResult(
            consensus=consensus,
            synthesis=synthesis,
            differences=differences,
            raw_content=content,
            synthesizer_model=synthesizer_model,
            message_count=self._message_count,
            method="tradeoff",
        )
