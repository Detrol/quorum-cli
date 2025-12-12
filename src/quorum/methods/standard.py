"""Standard method: 5-phase consensus-seeking discussion."""

from __future__ import annotations

import asyncio
import logging
import re
from collections import deque
from typing import AsyncIterator

from ..agents import (
    _make_valid_identifier,
    get_critique_prompt,
    get_final_position_prompt,
    get_phase1_prompt,
    get_standard_discussion_prompt,
    get_synthesis_prompt,
)
from ..clients import SystemMessage, UserMessage
from ..constants import (
    CRITIQUE_ERROR_MAX_LENGTH,
    MAX_DISCUSSION_HISTORY_MESSAGES,
)
from ..models import extract_api_error, get_pooled_client, remove_from_pool
from .base import (
    BaseMethodOrchestrator,
    CritiqueResponse,
    FinalPosition,
    IndependentAnswer,
    MessageType,
    SynthesisResult,
    TeamTextMessage,
    ThinkingComplete,
    ThinkingIndicator,
)

logger = logging.getLogger(__name__)

# Pre-compiled regex patterns for parsing model responses (English headers only)
# AI is instructed to always use English headers regardless of content language
_AGREEMENT_PATTERN = re.compile(r'AGREEMENTS?:\s*(.+?)(?=DISAGREEMENTS?:|MISSING:|$)', re.DOTALL | re.IGNORECASE)
_DISAGREEMENT_PATTERN = re.compile(r'DISAGREEMENTS?:\s*(.+?)(?=AGREEMENTS?:|MISSING:|$)', re.DOTALL | re.IGNORECASE)
_MISSING_PATTERN = re.compile(r'MISSING:\s*(.+?)(?=AGREEMENTS?:|DISAGREEMENTS?:|$)', re.DOTALL | re.IGNORECASE)
_POSITION_PATTERN = re.compile(r'POSITION:\s*(.+?)(?=CONFIDENCE:|$)', re.DOTALL | re.IGNORECASE)
_CONFIDENCE_PATTERN = re.compile(r'CONFIDENCE:\s*(HIGH|MEDIUM|LOW)', re.IGNORECASE)


class StandardMethod(BaseMethodOrchestrator):
    """Standard 5-phase consensus-seeking discussion.

    Phase 1: Independent Answers (parallel)
    Phase 2: Structured Critique (parallel)
    Phase 3: Discussion (sequential)
    Phase 4: Final Positions (parallel)
    Phase 5: Synthesis
    """

    @property
    def method_name(self) -> str:
        return "standard"

    @property
    def total_phases(self) -> int:
        return 5

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Standard-specific storage
        self._initial_responses: dict[str, str] = {}
        self._critiques: dict[str, CritiqueResponse] = {}
        self._final_positions: list[FinalPosition] = []

    async def run_stream(self, task: str) -> AsyncIterator[MessageType]:
        """Run 5-phase consensus discussion."""
        self._original_task = task
        self._agent_names = {_make_valid_identifier(m) for m in self.model_ids}
        num_participants = len(self.model_ids)

        # === PHASE 1: Independent answers (parallel) ===
        yield self._create_phase_marker(1, {"count": str(num_participants)})

        # Stream ThinkingComplete events and collect results
        async for item in self._run_phase1_streaming(task):
            if isinstance(item, ThinkingComplete):
                yield item
            else:
                # Tuple (agent_name, content) - collect results
                agent_name, content = item
                self._initial_responses[agent_name] = content

        # Yield IndependentAnswer messages in model order
        for model_id in self.model_ids:
            agent_name = _make_valid_identifier(model_id)
            if agent_name in self._initial_responses:
                yield IndependentAnswer(
                    source=model_id,
                    content=self._initial_responses[agent_name],
                )

        # === PHASE 2: Structured critique (parallel) ===
        yield self._create_phase_marker(2)

        self._critiques = await self._run_phase2_critique(task)

        for model_id in self.model_ids:
            agent_name = _make_valid_identifier(model_id)
            if agent_name in self._critiques:
                yield self._critiques[agent_name]

        # === PHASE 3: Discussion (sequential) ===
        yield self._create_phase_marker(3)

        async for message in self._run_phase3_discussion(task):
            self._message_count += 1
            yield message

        # === PHASE 4: Final positions (parallel) ===
        yield self._create_phase_marker(4)

        self._final_positions = await self._run_phase4_final_positions(task)

        for position in self._final_positions:
            yield position

        # === PHASE 5: AI Synthesis ===
        yield self._create_phase_marker(5)

        yield ThinkingIndicator(model=self._get_synthesizer_model())
        self._synthesis_result = await self._run_synthesis(task)
        yield self._synthesis_result

    # =========================================================================
    # Phase 1: Independent Answers
    # =========================================================================

    async def _run_phase1_streaming(
        self, task: str
    ) -> AsyncIterator[ThinkingComplete | tuple[str, str]]:
        """Phase 1: Get independent answers with streaming ThinkingComplete events.

        Yields ThinkingComplete events as each model finishes, followed by
        (agent_name, content) tuples for results.
        """
        num_participants = len(self.model_ids)
        phase1_prompt = get_phase1_prompt(num_participants)

        async def get_answer(model_id: str) -> tuple[str, str, str]:
            """Returns (model_id, agent_name, content).

            Uses pooled clients to avoid closing shared HTTP connections
            while other requests are still in progress.
            """
            from ..config import get_settings

            timeout = get_settings().model_timeout
            agent_name = _make_valid_identifier(model_id)
            try:
                # Use pooled client - reuses connections, doesn't close after use
                client = await get_pooled_client(model_id)
                response = await asyncio.wait_for(
                    client.create(
                        messages=[
                            SystemMessage(content=phase1_prompt, source="system"),
                            UserMessage(content=task, source="user"),
                        ]
                    ),
                    timeout=timeout,
                )
                content = self._extract_response_content(response)
                return (model_id, agent_name, content)
            except asyncio.TimeoutError:
                await remove_from_pool(model_id)
                return (model_id, agent_name, f"[Timeout: No response within {timeout}s]")
            except Exception as e:
                # Remove from pool on error - connection may be broken
                await remove_from_pool(model_id)
                return (model_id, agent_name, f"[Error: {extract_api_error(e)}]")

        # Create tasks and use as_completed for streaming
        tasks = [asyncio.create_task(get_answer(model_id)) for model_id in self.model_ids]
        results: list[tuple[str, str, str]] = []

        try:
            for future in asyncio.as_completed(tasks):
                model_id, agent_name, content = await future
                yield ThinkingComplete(model=model_id)
                results.append((model_id, agent_name, content))
        except asyncio.CancelledError:
            # Cancel all remaining tasks to prevent orphans
            for task in tasks:
                if not task.done():
                    task.cancel()
            raise

        # Yield all results after all completions
        for model_id, agent_name, content in results:
            yield (agent_name, content)

    async def _run_phase1_parallel(self, task: str) -> dict[str, str]:
        """Phase 1: Get independent answers (backward-compatible sync wrapper).

        This method wraps the streaming version and returns a dict for tests
        and any code that expects the original synchronous return format.
        """
        results: dict[str, str] = {}
        async for item in self._run_phase1_streaming(task):
            if isinstance(item, ThinkingComplete):
                # Skip ThinkingComplete events - just collecting results
                continue
            else:
                agent_name, content = item
                results[agent_name] = content
        return results

    # =========================================================================
    # Phase 2: Structured Critique
    # =========================================================================

    async def _run_phase2_critique(self, task: str) -> dict[str, CritiqueResponse]:
        """Phase 2: Get structured critiques from all models in parallel."""
        num_participants = len(self.model_ids)
        all_answers = self._format_all_initial_answers()

        async def get_critique(model_id: str) -> tuple[str, CritiqueResponse]:
            agent_name = _make_valid_identifier(model_id)
            own_answer = self._initial_responses.get(agent_name, "[No answer]")

            critique_prompt = get_critique_prompt(
                num_participants=num_participants,
                your_initial_answer=own_answer,
                all_initial_answers=all_answers,
            )

            try:
                client = await get_pooled_client(model_id)
                response = await client.create(
                    messages=[
                        SystemMessage(content=critique_prompt, source="system"),
                        UserMessage(content=f"Question: {task}\n\nProvide your structured critique.", source="user"),
                    ]
                )
                content = self._extract_response_content(response)
                critique = self._parse_critique(model_id, content)
                return (agent_name, critique)

            except Exception as e:
                return (agent_name, CritiqueResponse(
                    source=model_id,
                    agreements=f"[Error: {extract_api_error(e, max_length=CRITIQUE_ERROR_MAX_LENGTH)}]",
                    disagreements="",
                    missing="",
                    raw_content=str(e),
                ))

        tasks = [get_critique(model_id) for model_id in self.model_ids]
        results = await asyncio.gather(*tasks)
        return dict(results)

    def _parse_critique(self, source: str, content: str) -> CritiqueResponse:
        """Parse structured critique from model response."""
        agreements = ""
        disagreements = ""
        missing = ""

        agree_match = _AGREEMENT_PATTERN.search(content)
        disagree_match = _DISAGREEMENT_PATTERN.search(content)
        missing_match = _MISSING_PATTERN.search(content)

        if agree_match:
            agreements = agree_match.group(1).strip()
        if disagree_match:
            disagreements = disagree_match.group(1).strip()
        if missing_match:
            missing = missing_match.group(1).strip()

        if not agreements and not disagreements and not missing:
            logger.debug(
                "Critique parsing fallback for %s: no structured sections found, using raw content",
                source
            )
            agreements = content

        return CritiqueResponse(
            source=source,
            agreements=agreements,
            disagreements=disagreements,
            missing=missing,
            raw_content=content,
        )

    # =========================================================================
    # Phase 3: Discussion
    # =========================================================================

    async def _run_phase3_discussion(self, task: str) -> AsyncIterator[ThinkingIndicator | TeamTextMessage]:
        """Phase 3: Balanced consensus-seeking discussion with turn tracking.

        Uses a sliding window deque for discussion history to prevent
        unbounded memory growth in long discussions.
        """
        num_participants = len(self.model_ids)
        all_answers = self._format_all_initial_answers()
        all_critiques = self._format_all_critiques()
        # Use deque with maxlen to prevent unbounded memory growth
        discussion_history: deque[str] = deque(maxlen=MAX_DISCUSSION_HISTORY_MESSAGES)

        total_turns = self.max_discussion_turns

        for turn in range(total_turns):
            speaker_idx = turn % num_participants
            model_id = self.model_ids[speaker_idx]
            agent_name = _make_valid_identifier(model_id)
            own_answer = self._initial_responses.get(agent_name, "[No answer]")

            yield ThinkingIndicator(model=model_id)

            prompt = get_standard_discussion_prompt(
                num_participants=num_participants,
                your_initial_answer=own_answer,
                all_initial_answers=all_answers,
                all_critiques=all_critiques,
                current_turn=turn + 1,
                total_turns=total_turns,
                discussion_history="\n\n".join(discussion_history),
            )

            user_msg = f"Question: {task}\n\nContribute to the discussion."
            response = await self._get_model_response(model_id, prompt, user_msg)

            discussion_history.append(f"{self._display_name(model_id)}:\n{response}")

            yield self._create_team_message(model_id, response)

    # =========================================================================
    # Phase 4: Final Positions
    # =========================================================================

    async def _run_phase4_final_positions(self, task: str) -> list[FinalPosition]:
        """Phase 4: Get final positions with confidence from all models."""
        final_prompt = get_final_position_prompt(task)

        async def get_final_position(model_id: str) -> FinalPosition:
            try:
                client = await get_pooled_client(model_id)
                response = await client.create(
                    messages=[
                        SystemMessage(content=final_prompt, source="system"),
                        UserMessage(content="State your final position and confidence level.", source="user"),
                    ]
                )
                content = self._extract_response_content(response)
                return self._parse_final_position(model_id, content)

            except Exception as e:
                return FinalPosition(
                    source=model_id,
                    position=f"[Error: {extract_api_error(e)}]",
                    confidence="LOW",
                    raw_content=str(e),
                )

        tasks = [get_final_position(model_id) for model_id in self.model_ids]
        results = await asyncio.gather(*tasks)
        return list(results)

    def _parse_final_position(self, source: str, content: str) -> FinalPosition:
        """Parse final position and confidence from model response."""
        position = content
        confidence = "MEDIUM"

        pos_match = _POSITION_PATTERN.search(content)
        conf_match = _CONFIDENCE_PATTERN.search(content)

        if pos_match:
            position = pos_match.group(1).strip()
        else:
            logger.debug(
                "Final position parsing fallback for %s: no POSITION section, using raw content",
                source
            )

        if conf_match:
            confidence = conf_match.group(1).upper()
        else:
            logger.debug(
                "Confidence parsing fallback for %s: no CONFIDENCE found, defaulting to MEDIUM",
                source
            )

        return FinalPosition(
            source=source,
            position=position,
            confidence=confidence,
            raw_content=content,
        )

    # =========================================================================
    # Phase 5: Synthesis
    # =========================================================================

    async def _run_synthesis(self, task: str) -> SynthesisResult:
        """Phase 5: Use one model to synthesize all final positions."""
        num_participants = len(self.model_ids)
        all_positions = self._format_all_final_positions()

        synthesis_prompt = get_synthesis_prompt(
            original_question=task,
            num_participants=num_participants,
            all_positions=all_positions,
        )

        synthesizer_model = self._get_synthesizer_model()

        try:
            client = await get_pooled_client(synthesizer_model)
            response = await client.create(
                messages=[
                    SystemMessage(content=synthesis_prompt, source="system"),
                    UserMessage(
                        content="Analyze the final positions and provide your synthesis.",
                        source="user",
                    ),
                ]
            )
            content = self._extract_response_content(response)

            return self._parse_synthesis(
                content,
                synthesizer_model,
                method="standard",
                positions=self._final_positions,
                confidence_breakdown=self._count_confidence_levels(self._final_positions),
            )

        except Exception as e:
            return SynthesisResult(
                consensus="NO",
                synthesis=f"[Error during synthesis: {extract_api_error(e)}]",
                differences="Unable to determine due to error",
                raw_content=str(e),
                synthesizer_model=synthesizer_model,
                positions=self._final_positions,
                confidence_breakdown=self._count_confidence_levels(self._final_positions),
                message_count=self._message_count,
                method="standard",
            )

    # =========================================================================
    # Formatting Helpers
    # =========================================================================

    def _format_all_initial_answers(self) -> str:
        """Format all initial answers for prompts."""
        lines = []
        for model_id in self.model_ids:
            agent_name = _make_valid_identifier(model_id)
            answer = self._initial_responses.get(agent_name, "[No answer]")
            lines.append(f"--- {self._display_name(model_id)} ---\n{answer}\n")
        return "\n".join(lines)

    def _format_all_critiques(self) -> str:
        """Format all critiques for Phase 3 prompt."""
        lines = []
        for model_id in self.model_ids:
            agent_name = _make_valid_identifier(model_id)
            critique = self._critiques.get(agent_name)
            if critique:
                lines.append(
                    f"--- {self._display_name(model_id)}'s critique ---\n"
                    f"AGREEMENTS: {critique.agreements}\n"
                    f"DISAGREEMENTS: {critique.disagreements}\n"
                    f"MISSING: {critique.missing}\n"
                )
        return "\n".join(lines)

    def _format_all_final_positions(self) -> str:
        """Format all final positions for the synthesis prompt."""
        lines = []
        for pos in self._final_positions:
            display_name = self._display_name(pos.source)
            lines.append(
                f"--- {display_name} ---\n"
                f"POSITION: {pos.position}\n"
                f"CONFIDENCE: {pos.confidence}\n"
            )
        return "\n".join(lines)

    # =========================================================================
    # Result Accessors
    # =========================================================================

    def get_initial_responses(self) -> dict[str, str]:
        """Get all Phase 1 initial responses."""
        return self._initial_responses.copy()

    def get_critiques(self) -> dict[str, CritiqueResponse]:
        """Get all Phase 2 critiques."""
        return self._critiques.copy()

    def get_final_positions(self) -> list[FinalPosition]:
        """Get all Phase 4 final positions."""
        return self._final_positions.copy()
