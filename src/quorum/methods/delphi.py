"""Delphi method: Iterative anonymous estimation toward convergence."""

from __future__ import annotations

import logging
import re
from typing import AsyncIterator

from ..agents import (
    _make_valid_identifier,
    get_delphi_revision_prompt,
    get_delphi_round1_prompt,
    get_delphi_synthesis_prompt,
)
from ..models import extract_api_error
from .base import (
    BaseMethodOrchestrator,
    MessageType,
    SynthesisResult,
    ThinkingIndicator,
)

logger = logging.getLogger(__name__)


class DelphiMethod(BaseMethodOrchestrator):
    """Delphi method: Iterative anonymous estimates toward convergence.

    Based on RAND Corporation methodology (1950s-60s).
    Key principles: Anonymity, iterative rounds, controlled feedback, convergence.

    Phase 1: Round 1 - Independent Estimates (anonymous, parallel)
    Phase 2: Round 2 - Informed Revision (see group stats, revise)
    Phase 3: Round 3 - Final Revision (if needed)
    Phase 4: Synthesis - Aggregate final estimates
    """

    @property
    def method_name(self) -> str:
        return "delphi"

    @property
    def total_phases(self) -> int:
        return 4

    async def run_stream(self, task: str) -> AsyncIterator[MessageType]:
        """Run Delphi iterative estimation flow."""
        self._original_task = task
        max_rounds = 3

        round_estimates: list[dict[str, str]] = []

        # === PHASE 1: Round 1 - Independent Estimates ===
        yield self._create_phase_marker(1)

        round1_estimates = await self._run_delphi_round(task, 1, None, None)
        round_estimates.append(round1_estimates)

        for model_id in self.model_ids:
            agent_name = _make_valid_identifier(model_id)
            if agent_name in round1_estimates:
                self._message_count += 1
                yield self._create_team_message(model_id, round1_estimates[agent_name], "PANELIST")

        # === PHASE 2: Round 2 - Informed Revision ===
        yield self._create_phase_marker(2)

        group_estimates_r1 = self._format_anonymous_estimates(round1_estimates, 1)
        group_stats_r1 = self._calculate_group_statistics(round1_estimates)

        round2_estimates = await self._run_delphi_round(
            task, 2, round_estimates, group_estimates_r1, group_stats_r1
        )
        round_estimates.append(round2_estimates)

        for model_id in self.model_ids:
            agent_name = _make_valid_identifier(model_id)
            if agent_name in round2_estimates:
                self._message_count += 1
                yield self._create_team_message(model_id, round2_estimates[agent_name], "PANELIST")

        # Check convergence
        convergence_achieved = self._check_delphi_convergence(round2_estimates)

        # === PHASE 3: Round 3 - Final Revision (if not converged) ===
        if not convergence_achieved and max_rounds >= 3:
            yield self._create_phase_marker(3)

            group_estimates_r2 = self._format_anonymous_estimates(round2_estimates, 2)
            group_stats_r2 = self._calculate_group_statistics(round2_estimates)

            round3_estimates = await self._run_delphi_round(
                task, 3, round_estimates, group_estimates_r2, group_stats_r2
            )
            round_estimates.append(round3_estimates)

            for model_id in self.model_ids:
                agent_name = _make_valid_identifier(model_id)
                if agent_name in round3_estimates:
                    self._message_count += 1
                    yield self._create_team_message(model_id, round3_estimates[agent_name], "PANELIST")

        # === PHASE 4: Synthesis - Aggregate Estimates ===
        yield self._create_phase_marker(4)

        yield ThinkingIndicator(model=self._get_synthesizer_model())
        self._synthesis_result = await self._run_delphi_synthesis(task, round_estimates)
        yield self._synthesis_result

    async def _run_delphi_round(
        self,
        task: str,
        round_number: int,
        previous_rounds: list[dict[str, str]] | None,
        group_estimates: str | None = None,
        group_statistics: str | None = None,
    ) -> dict[str, str]:
        """Run a single Delphi round - all panelists respond in parallel."""
        num_participants = len(self.model_ids)

        async def get_estimate(model_id: str) -> tuple[str, str]:
            agent_name = _make_valid_identifier(model_id)

            if round_number == 1:
                prompt = get_delphi_round1_prompt(num_participants, task)
                user_msg = task
            else:
                previous_estimate = ""
                if previous_rounds:
                    prev_round = previous_rounds[-1]
                    previous_estimate = prev_round.get(agent_name, "[No previous estimate]")

                prompt = get_delphi_revision_prompt(
                    num_participants=num_participants,
                    round_number=round_number,
                    your_previous_estimate=previous_estimate,
                    group_estimates=group_estimates or "",
                    group_statistics=group_statistics or "",
                )
                user_msg = f"Question: {task}\n\nRevise your estimate if warranted."

            try:
                response = await self._get_model_response(model_id, prompt, user_msg)
                return (agent_name, response)
            except Exception as e:
                return (agent_name, f"[Error: {extract_api_error(e)}]")

        import asyncio
        tasks = [get_estimate(model_id) for model_id in self.model_ids]
        results = await asyncio.gather(*tasks)
        return dict(results)

    def _format_anonymous_estimates(self, estimates: dict[str, str], round_num: int) -> str:
        """Format estimates anonymously (Panelist A, B, C...)."""
        lines = []
        for i, (_, estimate) in enumerate(estimates.items()):
            panelist_letter = chr(65 + i)
            lines.append(f"Panelist {panelist_letter} (Round {round_num}):\n{estimate}\n")
        return "\n".join(lines)

    def _calculate_group_statistics(self, estimates: dict[str, str]) -> str:
        """Calculate simple statistics from estimates."""
        confidence_counts = self._extract_confidence_from_estimates(estimates)

        total = len(estimates)
        return (
            f"Number of panelists: {total}\n"
            f"Confidence distribution: HIGH={confidence_counts['HIGH']}, "
            f"MEDIUM={confidence_counts['MEDIUM']}, LOW={confidence_counts['LOW']}"
        )

    def _extract_confidence_from_estimates(self, estimates: dict[str, str]) -> dict[str, int]:
        """Extract confidence levels from Delphi estimates."""
        confidence_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for estimate in estimates.values():
            conf_match = re.search(
                r'CONFIDENCE:\s*(HIGH|MEDIUM|LOW)',
                estimate, re.IGNORECASE
            )
            if conf_match:
                confidence_counts[conf_match.group(1).upper()] += 1
            else:
                # Fallback: check for raw values in text
                estimate_upper = estimate.upper()
                if "HIGH" in estimate_upper:
                    confidence_counts["HIGH"] += 1
                elif "LOW" in estimate_upper:
                    confidence_counts["LOW"] += 1
                elif "MEDIUM" in estimate_upper:
                    confidence_counts["MEDIUM"] += 1
        return confidence_counts

    def _check_delphi_convergence(self, estimates: dict[str, str]) -> bool:
        """Check if estimates have converged sufficiently."""
        unchanged_count = sum(
            1 for est in estimates.values()
            if "UNCHANGED" in est.upper()
        )
        return unchanged_count >= len(estimates) * 0.7

    async def _run_delphi_synthesis(
        self, task: str, round_estimates: list[dict[str, str]]
    ) -> SynthesisResult:
        """Synthesize Delphi results into aggregated estimate."""
        synthesizer_model = self._get_synthesizer_model()
        num_participants = len(self.model_ids)

        final_round = round_estimates[-1]
        final_estimates = self._format_anonymous_estimates(final_round, len(round_estimates))
        confidence_breakdown = self._extract_confidence_from_estimates(final_round)

        history_lines = []
        for round_num, round_data in enumerate(round_estimates, 1):
            history_lines.append(f"=== ROUND {round_num} ===")
            history_lines.append(self._format_anonymous_estimates(round_data, round_num))
        estimate_history = "\n".join(history_lines)

        prompt = get_delphi_synthesis_prompt(
            question=task,
            num_participants=num_participants,
            final_estimates=final_estimates,
            estimate_history=estimate_history,
        )

        try:
            response = await self._get_model_response(
                synthesizer_model, prompt, "Produce the aggregated estimate."
            )
            return self._parse_delphi_synthesis(response, synthesizer_model, confidence_breakdown)
        except Exception as e:
            return SynthesisResult(
                consensus="PARTIAL",
                synthesis=f"[Error during aggregation: {extract_api_error(e)}]",
                differences="Unable to determine due to error",
                raw_content=str(e),
                synthesizer_model=synthesizer_model,
                message_count=self._message_count,
                method="delphi",
                confidence_breakdown=confidence_breakdown,
            )

    def _parse_delphi_synthesis(
        self, content: str, synthesizer_model: str, confidence_breakdown: dict[str, int]
    ) -> SynthesisResult:
        """Parse Delphi synthesis response."""
        consensus = "PARTIAL"
        synthesis = ""
        differences = ""

        conv_match = re.search(
            r'CONVERGENCE:\s*(YES|PARTIAL|NO)',
            content, re.IGNORECASE
        )
        if conv_match:
            consensus = conv_match.group(1).upper()

        agg_match = re.search(
            r'AGGREGATED ESTIMATE:\s*(.+?)(?=KEY FACTORS:|OUTLIER PERSPECTIVES?:|$)',
            content, re.DOTALL | re.IGNORECASE
        )
        if agg_match:
            synthesis = agg_match.group(1).strip()

        outlier_match = re.search(
            r'OUTLIER PERSPECTIVES?:\s*(.+?)(?=CONVERGENCE:|AGGREGATED ESTIMATE:|KEY FACTORS:|$)',
            content, re.DOTALL | re.IGNORECASE
        )
        if outlier_match:
            differences = outlier_match.group(1).strip()

        if not synthesis:
            logger.debug(
                "Delphi synthesis parsing fallback for %s: no AGGREGATED ESTIMATE found, using raw content",
                synthesizer_model
            )
            synthesis = content

        return SynthesisResult(
            consensus=consensus,
            synthesis=synthesis,
            differences=differences if differences else "None - strong convergence",
            raw_content=content,
            synthesizer_model=synthesizer_model,
            message_count=self._message_count,
            method="delphi",
            confidence_breakdown=confidence_breakdown,
        )
