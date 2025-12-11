"""Advocate method: Devil's advocate cross-examination."""

from __future__ import annotations

from collections import deque
from typing import AsyncIterator

from ..agents import (
    get_advocate_examined_prompt,
    get_advocate_examiner_prompt,
    get_advocate_verdict_prompt,
    get_language_instruction,
)
from ..constants import MAX_DISCUSSION_HISTORY_MESSAGES
from .base import (
    BaseMethodOrchestrator,
    MessageType,
    SynthesisResult,
    ThinkingIndicator,
)


class AdvocateMethod(BaseMethodOrchestrator):
    """Authentic Advocatus Diaboli: Cross-examination to test reasoning.

    Based on the Catholic Church's "Promoter of the Faith" who examined
    candidates for sainthood through rigorous questioning.

    Phase 1: Initial Positions (defenders state their claims)
    Phase 2: Cross-Examination (advocate examines each defender)
    Phase 3: Verdict (advocate delivers assessment)
    """

    @property
    def method_name(self) -> str:
        return "advocate"

    @property
    def total_phases(self) -> int:
        return 3

    async def run_stream(self, task: str) -> AsyncIterator[MessageType]:
        """Run advocate cross-examination flow."""
        self._original_task = task
        discussion_history: deque[str] = deque(maxlen=MAX_DISCUSSION_HISTORY_MESSAGES)

        # Get advocate from role assignments or default to last model
        if self.role_assignments and "Advocate" in self.role_assignments:
            advocate_model = self.role_assignments["Advocate"][0]
        else:
            advocate_model = self.model_ids[-1]

        defenders = [m for m in self.model_ids if m != advocate_model]
        language_inst = get_language_instruction()

        # === PHASE 1: Initial Positions ===
        yield self._create_phase_marker(1)

        for model_id in defenders:
            yield ThinkingIndicator(model=model_id)

            prompt = f"""{language_inst}

You are participating in a formal examination process (Advocatus Diaboli).
Your claims will be cross-examined by a Devil's Advocate.

State your position on the question clearly. Include:
1. Your main claim or thesis
2. Key supporting arguments or evidence
3. Any important qualifications or nuances

Be clear and direct - these claims will be rigorously examined."""

            user_msg = f"Question: {task}\n\nState your position."
            response = await self._get_model_response(model_id, prompt, user_msg)

            discussion_history.append(f"[DEFENDER] {self._display_name(model_id)} (Initial Position):\n{response}")
            self._message_count += 1

            yield self._create_team_message(model_id, response, "DEFENDER")

        # === PHASE 2: Cross-Examination ===
        yield self._create_phase_marker(2)

        total_examinations = max(len(defenders) * 2, self.max_discussion_turns)
        examined_complete: set[str] = set()

        for exam_num in range(total_examinations):
            if len(examined_complete) >= len(defenders):
                break

            current_defender = defenders[exam_num % len(defenders)]
            if current_defender in examined_complete:
                continue

            current_round = (exam_num // len(defenders)) + 1
            total_rounds = (total_examinations // len(defenders)) + 1

            # Advocate examines
            yield ThinkingIndicator(model=advocate_model)

            examiner_prompt = get_advocate_examiner_prompt(
                target_name=self._display_name(current_defender),
                discussion_history="\n\n".join(discussion_history),
                current_round=current_round,
                total_rounds=total_rounds,
            )

            examination = await self._get_model_response(
                advocate_model,
                examiner_prompt,
                f"Examine {self._display_name(current_defender)}'s claims.",
            )

            discussion_history.append(
                f"[ADVOCATE → {self._display_name(current_defender)}] "
                f"{self._display_name(advocate_model)} (Examination):\n{examination}"
            )
            self._message_count += 1

            yield self._create_team_message(advocate_model, examination, "ADVOCATE")

            if "EXAMINATION COMPLETE" in examination.upper():
                examined_complete.add(current_defender)
                continue

            # Defender responds
            yield ThinkingIndicator(model=current_defender)

            examined_prompt = get_advocate_examined_prompt(
                discussion_history="\n\n".join(discussion_history),
            )

            response = await self._get_model_response(
                current_defender,
                examined_prompt,
                "Answer the advocate's question.",
            )

            discussion_history.append(
                f"[DEFENDER] {self._display_name(current_defender)} (Response):\n{response}"
            )
            self._message_count += 1

            yield self._create_team_message(current_defender, response, "DEFENDER")

        # === PHASE 3: Verdict ===
        yield self._create_phase_marker(3)

        yield ThinkingIndicator(model=advocate_model)

        verdict_prompt = get_advocate_verdict_prompt(
            discussion_history="\n\n".join(discussion_history),
        )

        verdict = await self._get_model_response(
            advocate_model,
            verdict_prompt,
            "Deliver your verdict on the examination.",
        )

        discussion_history.append(f"[ADVOCATE] {self._display_name(advocate_model)} (Verdict):\n{verdict}")
        self._message_count += 1

        # The verdict IS the synthesis - no separate API call needed
        self._synthesis_result = SynthesisResult(
            consensus="PARTIAL",
            synthesis=verdict,
            differences="See verdict above for unresolved questions.",
            raw_content=verdict,
            synthesizer_model=advocate_model,
            message_count=self._message_count,
            method="advocate",
        )
        yield self._synthesis_result
