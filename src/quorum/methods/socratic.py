"""Socratic method: Elenchus through questioning."""

from __future__ import annotations

from collections import deque
from typing import AsyncIterator, Sequence

from ..agents import (
    get_language_instruction,
    get_socratic_questioner_prompt,
    get_socratic_respondent_prompt,
)
from ..clients import SystemMessage, UserMessage
from ..constants import MAX_DISCUSSION_HISTORY_MESSAGES
from ..models import extract_api_error, get_pooled_client
from .base import (
    BaseMethodOrchestrator,
    MessageType,
    SynthesisResult,
    ThinkingIndicator,
)


class SocraticMethod(BaseMethodOrchestrator):
    """Socratic dialogue: Critical examination through questioning.

    Phase 1: Initial Thesis (first model presents position)
    Phase 2: Socratic Inquiry (rotating questioner probes)
    Phase 3: Aporia & Insights (what was discovered?)

    The goal is deeper understanding, not consensus.
    """

    @property
    def method_name(self) -> str:
        return "socratic"

    @property
    def total_phases(self) -> int:
        return 3

    async def run_stream(self, task: str) -> AsyncIterator[MessageType]:
        """Run Socratic dialogue flow."""
        self._original_task = task
        num_participants = len(self.model_ids)
        discussion_history: deque[str] = deque(maxlen=MAX_DISCUSSION_HISTORY_MESSAGES)

        # Determine thesis presenter
        if self.role_assignments and "Respondent" in self.role_assignments:
            thesis_presenter = self.role_assignments["Respondent"][0]
            questioners = [m for m in self.model_ids if m != thesis_presenter]
        else:
            thesis_presenter = self.model_ids[0]
            questioners = self.model_ids[1:]

        # === PHASE 1: Initial Thesis ===
        yield self._create_phase_marker(1)
        yield ThinkingIndicator(model=thesis_presenter)

        thesis_prompt = """You are beginning a Socratic dialogue. Like Socrates' interlocutors, you will present an initial thesis that will be examined through questioning.

Present your initial position on the question. Be clear and definitive - this will be the starting point for critical examination.

Remember: In Socratic dialogue, initial positions are often refined or even overturned through questioning. Be willing to have your ideas examined."""

        user_msg = f"Question: {task}\n\nPresent your initial thesis."
        thesis = await self._get_model_response(thesis_presenter, thesis_prompt, user_msg)

        discussion_history.append(f"[INITIAL THESIS] {self._display_name(thesis_presenter)}:\n{thesis}")
        self._message_count += 1

        yield self._create_team_message(thesis_presenter, thesis, "RESPONDENT")

        # === PHASE 2: Socratic Inquiry ===
        yield self._create_phase_marker(2)

        total_rounds = max(3, self.max_discussion_turns // 2)
        respondent_model = thesis_presenter

        for round_num in range(total_rounds):
            current_round = round_num + 1
            questioner_model = questioners[round_num % len(questioners)]

            # Questioner asks
            yield ThinkingIndicator(model=questioner_model)

            questioner_prompt = get_socratic_questioner_prompt(
                num_participants=num_participants,
                all_initial_answers=thesis,
                discussion_history="\n\n".join(discussion_history),
                respondent_name=self._display_name(respondent_model),
                current_round=current_round,
                total_rounds=total_rounds,
            )

            question = await self._get_model_response(
                questioner_model,
                questioner_prompt,
                "Ask ONE probing question that exposes an assumption or potential contradiction.",
            )

            discussion_history.append(f"[QUESTIONER] {self._display_name(questioner_model)}:\n{question}")
            self._message_count += 1

            yield self._create_team_message(questioner_model, question, "QUESTIONER")

            # Respondent answers
            yield ThinkingIndicator(model=respondent_model)

            respondent_prompt = get_socratic_respondent_prompt(
                num_participants=num_participants,
                all_initial_answers=thesis,
                question=question,
                discussion_history="\n\n".join(discussion_history),
                current_round=current_round,
                total_rounds=total_rounds,
            )

            answer = await self._get_model_response(
                respondent_model,
                respondent_prompt,
                "Answer the question thoughtfully. If it exposes a weakness in your position, acknowledge it.",
            )

            discussion_history.append(f"[RESPONDENT] {self._display_name(respondent_model)}:\n{answer}")
            self._message_count += 1

            yield self._create_team_message(respondent_model, answer, "RESPONDENT")

        # === PHASE 3: Aporia ===
        yield self._create_phase_marker(3)

        yield ThinkingIndicator(model=thesis_presenter)

        language_inst = get_language_instruction()
        aporia_prompt = f"""{language_inst}

The Socratic examination of your thesis is complete.

YOUR ORIGINAL THESIS:
{thesis}

DIALOGUE TRANSCRIPT:
{chr(10).join(discussion_history)}

In the spirit of authentic Socratic dialogue, reflect honestly:
1. What assumptions in your thesis were exposed that you hadn't recognized?
2. What contradictions or weaknesses did the questioning reveal?
3. Has your position changed, strengthened, or do you now see its limits more clearly?
4. What do you now realize you don't know (aporia)?

Be intellectually honest. Socratic dialogue aims at truth, not winning."""

        aporia_reflection = await self._get_model_response(
            thesis_presenter,
            aporia_prompt,
            "Reflect on what the examination revealed about your thesis.",
        )

        discussion_history.append(f"[APORIA] {self._display_name(thesis_presenter)}:\n{aporia_reflection}")
        self._message_count += 1

        yield self._create_team_message(thesis_presenter, aporia_reflection, "RESPONDENT")

        # Questioner summaries
        for questioner in questioners:
            yield ThinkingIndicator(model=questioner)

            summary_prompt = f"""{language_inst}

You have been the questioner (like Socrates) examining {self._display_name(thesis_presenter)}'s thesis.

DIALOGUE TRANSCRIPT:
{chr(10).join(discussion_history)}

Briefly summarize (as Socrates would):
1. What key assumptions or contradictions did your questioning expose?
2. Did the examination lead to aporia (productive recognition of not-knowing)?

Do NOT state your own position on the question. Your role was to examine, not to argue."""

            summary = await self._get_model_response(
                questioner,
                summary_prompt,
                "Summarize what your examination revealed.",
            )

            discussion_history.append(f"[EXAMINATION SUMMARY] {self._display_name(questioner)}:\n{summary}")
            self._message_count += 1

            yield self._create_team_message(questioner, summary, "QUESTIONER")

        # Synthesis
        yield ThinkingIndicator(model=self._get_synthesizer_model())
        self._synthesis_result = await self._run_socratic_synthesis(task, discussion_history)
        yield self._synthesis_result

    async def _run_socratic_synthesis(
        self, task: str, discussion_history: Sequence[str]
    ) -> SynthesisResult:
        """Synthesize the outcomes of the Socratic dialogue."""
        synthesizer_model = self._get_synthesizer_model()
        language_inst = get_language_instruction()

        synthesis_prompt = f"""{language_inst}

You are summarizing an authentic Socratic dialogue on: "{task}"

DIALOGUE TRANSCRIPT:
{chr(10).join(discussion_history)}

Analyze what was discovered through this examination:
1. How did the original thesis evolve through questioning?
2. What key assumptions were exposed or challenged?
3. Did the examination lead to aporia (productive recognition of the limits of knowledge)?

Provide your synthesis in this format:
APORIA_REACHED: [YES/PARTIAL/NO] (did the examination reveal gaps in understanding?)
SYNTHESIS: [What the Socratic examination revealed - focus on the journey of inquiry, not conclusions]
OPEN_QUESTIONS: [Questions that remain unresolved - this is valuable in Socratic dialogue]"""

        try:
            client = await get_pooled_client(synthesizer_model)
            response = await client.create(
                messages=[
                    SystemMessage(content=synthesis_prompt, source="system"),
                    UserMessage(content="Synthesize the dialogue outcomes.", source="user"),
                ]
            )
            content = self._extract_response_content(response)

            return self._parse_synthesis(content, synthesizer_model, method="socratic")

        except Exception as e:
            return SynthesisResult(
                consensus="PARTIAL",
                synthesis=f"[Error during synthesis: {extract_api_error(e)}]",
                differences="Unable to determine due to error",
                raw_content=str(e),
                synthesizer_model=synthesizer_model,
                message_count=self._message_count,
                method="socratic",
            )
