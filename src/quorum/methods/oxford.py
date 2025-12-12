"""Oxford method: Parliamentary debate (FOR/AGAINST)."""

from __future__ import annotations

from collections import deque
from typing import AsyncIterator

from ..agents import get_language_instruction, get_oxford_prompt
from ..clients import SystemMessage, UserMessage
from ..constants import MAX_DISCUSSION_HISTORY_MESSAGES
from ..models import extract_api_error, get_pooled_client
from .base import (
    BaseMethodOrchestrator,
    MessageType,
    SynthesisResult,
    ThinkingIndicator,
)


class OxfordMethod(BaseMethodOrchestrator):
    """Oxford Union parliamentary debate.

    Phase 1: Opening Statements (alternating FOR/AGAINST)
    Phase 2: Rebuttals (alternating, respond to opposing side)
    Phase 3: Closing Arguments (one speaker per side)
    Phase 4: Judgement (synthesis model evaluates debate)
    """

    @property
    def method_name(self) -> str:
        return "oxford"

    @property
    def total_phases(self) -> int:
        return 4

    async def run_stream(self, task: str) -> AsyncIterator[MessageType]:
        """Run Oxford debate flow."""
        self._original_task = task
        num_participants = len(self.model_ids)
        discussion_history: deque[str] = deque(maxlen=MAX_DISCUSSION_HISTORY_MESSAGES)

        # Get role assignments
        if self.role_assignments and "FOR" in self.role_assignments:
            for_team = list(self.role_assignments["FOR"])
            against_team = list(self.role_assignments["AGAINST"])
        else:
            for_team = [m for i, m in enumerate(self.model_ids) if i % 2 == 0]
            against_team = [m for i, m in enumerate(self.model_ids) if i % 2 == 1]

        alternating_speakers = self._get_alternating_order(for_team, against_team)

        # === PHASE 1: Opening Statements ===
        yield self._create_phase_marker(1)

        for model_id, role in alternating_speakers:
            yield ThinkingIndicator(model=model_id)

            prompt = get_oxford_prompt(
                round_type="opening",
                role=role,
                num_participants=num_participants,
                all_initial_answers="",
                all_critiques="",
                discussion_history="\n\n".join(discussion_history),
            )

            user_msg = f"Motion: {task}\n\nDeliver your opening statement arguing {role} the motion."
            response = await self._get_model_response(model_id, prompt, user_msg)

            discussion_history.append(f"[{role}] {self._display_name(model_id)} (Opening):\n{response}")
            self._message_count += 1

            yield self._create_team_message(model_id, response, role, "opening")

        # === PHASE 2: Rebuttals ===
        yield self._create_phase_marker(2)

        for model_id, role in alternating_speakers:
            yield ThinkingIndicator(model=model_id)

            prompt = get_oxford_prompt(
                round_type="rebuttal",
                role=role,
                num_participants=num_participants,
                all_initial_answers="",
                all_critiques="",
                discussion_history="\n\n".join(discussion_history),
            )

            user_msg = "Address the opposing side's arguments and defend your position."
            response = await self._get_model_response(model_id, prompt, user_msg)

            discussion_history.append(f"[{role}] {self._display_name(model_id)} (Rebuttal):\n{response}")
            self._message_count += 1

            yield self._create_team_message(model_id, response, role, "rebuttal")

        # === PHASE 3: Closing Arguments ===
        yield self._create_phase_marker(3)

        closing_speakers = [
            (for_team[0], "FOR") if for_team else None,
            (against_team[0], "AGAINST") if against_team else None,
        ]

        for speaker in closing_speakers:
            if speaker is None:
                continue
            model_id, role = speaker

            yield ThinkingIndicator(model=model_id)

            prompt = get_oxford_prompt(
                round_type="closing",
                role=role,
                num_participants=num_participants,
                all_initial_answers="",
                all_critiques="",
                discussion_history="\n\n".join(discussion_history),
            )

            user_msg = "Deliver your closing argument, summarizing your side's strongest points."
            response = await self._get_model_response(model_id, prompt, user_msg)

            discussion_history.append(f"[{role}] {self._display_name(model_id)} (Closing):\n{response}")
            self._message_count += 1

            yield self._create_team_message(model_id, response, role, "closing")

        # === PHASE 4: Judgement ===
        yield self._create_phase_marker(4)

        yield ThinkingIndicator(model=self._get_synthesizer_model())
        self._synthesis_result = await self._run_oxford_judgement(task, discussion_history)
        yield self._synthesis_result

    def _get_alternating_order(
        self, for_list: list[str], against_list: list[str]
    ) -> list[tuple[str, str]]:
        """Return alternating speakers: (model_id, role)."""
        result = []
        max_len = max(len(for_list), len(against_list))
        for i in range(max_len):
            if i < len(for_list):
                result.append((for_list[i], "FOR"))
            if i < len(against_list):
                result.append((against_list[i], "AGAINST"))
        return result

    async def _run_oxford_judgement(
        self, task: str, debate_history: list[str]
    ) -> SynthesisResult:
        """Evaluate which side argued more effectively."""
        synthesizer_model = self._get_synthesizer_model()
        language_inst = get_language_instruction()

        judgement_prompt = f"""{language_inst}

You are judging an Oxford-style debate on the motion: "{task}"

DEBATE TRANSCRIPT:
{chr(10).join(debate_history)}

Your task is to evaluate which side argued more effectively. Consider:
1. Strength of arguments presented
2. Effectiveness of rebuttals
3. Use of evidence and reasoning
4. Persuasiveness of closing statements

Provide your judgement in this format:
CONSENSUS: [FOR/AGAINST/PARTIAL] (which side was more convincing, or PARTIAL if too close to call)
SYNTHESIS: [Your analysis of the key arguments and why one side was more effective]
DIFFERENCES: [Note the main points of contention that remained unresolved]"""

        try:
            client = await get_pooled_client(synthesizer_model)
            response = await client.create(
                messages=[
                    SystemMessage(content=judgement_prompt, source="system"),
                    UserMessage(content="Deliver your judgement.", source="user"),
                ]
            )
            content = self._extract_response_content(response)

            return self._parse_synthesis(content, synthesizer_model, method="oxford")

        except Exception as e:
            return SynthesisResult(
                consensus="PARTIAL",
                synthesis=f"[Error during judgement: {extract_api_error(e)}]",
                method="oxford",
                differences="Unable to determine due to error",
                raw_content=str(e),
                synthesizer_model=synthesizer_model,
                message_count=self._message_count,
            )
