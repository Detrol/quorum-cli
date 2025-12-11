"""Agent definitions for multi-model consensus."""

from __future__ import annotations

from .config import get_settings


def get_language_instruction() -> str:
    """Get language instruction based on config.

    Returns:
        Instruction string for prompt - either match question language
        or use configured default language. Headers always in English.
    """
    settings = get_settings()
    if settings.default_language:
        return (
            f"LANGUAGE: Respond in {settings.default_language}. "
            "IMPORTANT: Always use ENGLISH for section headers and labels "
            "(POSITION:, CONFIDENCE:, CONSENSUS:, AGREEMENTS:, etc.). "
            "Only the content/analysis should be in the target language."
        )
    return (
        "LANGUAGE: Respond in the same language as the question. "
        "IMPORTANT: Always use ENGLISH for section headers and labels "
        "(POSITION:, CONFIDENCE:, CONSENSUS:, AGREEMENTS:, etc.). "
        "Only the content/analysis should be in the target language."
    )


# =============================================================================
# Markdown formatting instruction (shared across prompts)
# =============================================================================
MARKDOWN_INSTRUCTION = """
FORMAT YOUR RESPONSE WITH MARKDOWN:
- Use ## headers for main sections
- Use **bold** for key terms and important points
- Use bullet points (- or *) for lists
- Use `code` for technical terms, commands, or short code
- Use ```language for multi-line code blocks (close with ```)
- Use tables for comparisons: | Header1 | Header2 |
- Structure your response logically with clear sections

MATH AND SCIENTIFIC NOTATION:
- Use Unicode characters directly instead of LaTeX notation
- Subscripts: CO₂, H₂O, fₗ, nₑ (NOT $CO_2$ or \\(f_l\\))
- Superscripts: 10⁻³, x², E=mc² (NOT $10^{-3}$ or \\(x^2\\))
- Greek letters: α, β, γ, δ, π, Σ, Ω (NOT \\alpha, $\\pi$)
- Symbols: ≈, ≠, ≤, ≥, →, ×, ÷, ∞ (NOT \\approx, \\rightarrow)
- This ensures proper display in all environments"""

# =============================================================================
# PHASE 1: Independent answer prompt (no context of others)
# =============================================================================
PHASE1_PROMPT = """{language_instruction}

You are an AI model participating in a {num_participants}-model consensus discussion.
Your answer will be shared with other AI models for critique and discussion.

PHASE 1 - INDEPENDENT ANSWER
You are answering FIRST, without seeing others' responses.

IMPORTANT:
- Do NOT address a human user
- Do NOT ask for clarification or more information
- Just provide your complete analysis
{markdown_instruction}

Guidelines:
- Provide YOUR independent viewpoint
- Explain your reasoning clearly
- Be confident in your analysis

Answer the question directly."""


# =============================================================================
# PHASE 2: Structured critique prompt (analyze all answers critically)
# =============================================================================
CRITIQUE_PROMPT = """{language_instruction}

You are an AI model critiquing answers from other AI models.

YOUR ORIGINAL ANSWER (Phase 1):
{your_initial_answer}

ALL ANSWERS FROM THE {num_participants} AI MODELS:
{all_initial_answers}

PHASE 2 - STRUCTURED CRITIQUE
Analyze ALL answers critically, including your own.
Reference other models by name (e.g., "gpt-5's point about X is strong").

You MUST identify:
1. AGREEMENTS - What points do you agree with? Reference which model.
2. DISAGREEMENTS - What do you disagree with or find weak?
3. MISSING - What important aspects were NOT addressed by anyone?

Format your response EXACTLY as:
AGREEMENTS: [specific points, reference which model]
DISAGREEMENTS: [specific weaknesses]
MISSING: [what no one addressed]

Be genuinely critical. Do NOT just agree with everything."""


# =============================================================================
# PHASE 3: Discussion prompts (method-specific)
# =============================================================================

# Standard method - balanced consensus-seeking discussion
DISCUSSION_PROMPT_STANDARD = """{language_instruction}

You are an AI model in a {num_participants}-model discussion.
You are discussing with OTHER AI MODELS - not with a human user.

DISCUSSION PROGRESS: Turn {current_turn} of {total_turns}
{turn_guidance}

CRITICAL RULES:
- Address other models BY NAME (e.g., "I agree with Claude's point about...")
- Do NOT ask the user for more information
- Do NOT end with "let me know..." or "if you want..."
- Keep your response SHORT - make ONE focused point
- Use **bold** for key terms and headers for sections

YOUR ORIGINAL ANSWER:
{your_initial_answer}

ALL ANSWERS:
{all_initial_answers}

ALL CRITIQUES:
{all_critiques}

{discussion_history_section}

PHASE 3 - DISCUSSION
Make ONE contribution to move the discussion forward:
- Address a disagreement raised in the critiques, OR
- Propose how to incorporate something that was missing, OR
- Build on an agreement to synthesize a better answer

Be brief and direct. Address the other models, not a user."""

# Valid methods for reference
VALID_METHODS = {"standard", "oxford", "advocate", "socratic", "delphi", "brainstorm", "tradeoff"}

# Method requirements for model count validation
METHOD_REQUIREMENTS = {
    "standard": {"min": 2, "even_only": False},
    "oxford": {"min": 2, "even_only": True},
    "advocate": {"min": 3, "even_only": False},
    "socratic": {"min": 2, "even_only": False},
    "delphi": {"min": 3, "even_only": False},      # 3+ for meaningful aggregation
    "brainstorm": {"min": 2, "even_only": False},  # 2+ for idea building
    "tradeoff": {"min": 2, "even_only": False},    # 2+ neutral evaluators
}


def get_role_assignments(method: str, model_ids: list[str]) -> dict[str, list[str]] | None:
    """Get role assignments for a method.

    Args:
        method: Discussion method name.
        model_ids: List of selected model IDs.

    Returns:
        Dict mapping role names to lists of model IDs, or None if method
        doesn't have explicit roles (e.g., standard).
    """
    if method == "oxford":
        for_team = [m for i, m in enumerate(model_ids) if i % 2 == 0]
        against_team = [m for i, m in enumerate(model_ids) if i % 2 == 1]
        return {"FOR": for_team, "AGAINST": against_team}

    elif method == "advocate":
        if len(model_ids) < 2:
            return None
        defenders = model_ids[:-1]
        advocate = [model_ids[-1]]
        return {"Defenders": defenders, "Advocate": advocate}

    elif method == "socratic":
        # First model is the respondent (presents thesis), rest are questioners
        if len(model_ids) < 2:
            return None
        respondent = [model_ids[0]]
        questioners = model_ids[1:]
        return {"Respondent": respondent, "Questioners": questioners}

    elif method == "delphi":
        # All models are equal "Panelists" - no explicit role assignment
        return {"Panelists": model_ids}

    elif method == "brainstorm":
        # All models are equal "Ideators" - no explicit role assignment
        return {"Ideators": model_ids}

    elif method == "tradeoff":
        # All models are neutral "Evaluators" - no explicit role assignment
        return {"Evaluators": model_ids}

    return None


def swap_teams(assignments: dict[str, list[str]]) -> dict[str, list[str]]:
    """Swap team assignments (FOR<->AGAINST, etc).

    Args:
        assignments: Current role assignments.

    Returns:
        Swapped role assignments.
    """
    if "FOR" in assignments and "AGAINST" in assignments:
        return {"FOR": assignments["AGAINST"], "AGAINST": assignments["FOR"]}

    elif "Defenders" in assignments and "Advocate" in assignments:
        # For advocate, rotate who is the advocate
        defenders = assignments["Defenders"]
        advocate = assignments["Advocate"]
        # Move current advocate to defenders, last defender becomes advocate
        new_defenders = advocate + defenders[:-1]
        new_advocate = [defenders[-1]] if defenders else advocate
        return {"Defenders": new_defenders, "Advocate": new_advocate}

    return assignments


def validate_method_model_count(method: str, num_models: int) -> tuple[bool, str | None]:
    """Validate that the number of models is allowed for the method.

    Args:
        method: Discussion method name.
        num_models: Number of selected models.

    Returns:
        (True, None) if valid, (False, error_message) otherwise.
    """
    req = METHOD_REQUIREMENTS.get(method)
    if not req:
        return True, None

    if num_models < req["min"]:
        return False, f"{method.capitalize()} requires at least {req['min']} models"

    if req["even_only"] and num_models % 2 != 0:
        return False, "Oxford requires an even number of models for balanced FOR/AGAINST teams"

    return True, None


# =============================================================================
# PHASE 3: Dynamic prompt functions for method-specific behavior
# =============================================================================

# --- OXFORD: Three-phase formal debate ---

OXFORD_PROMPT_OPENING = """{language_instruction}

You are in a formal Oxford-style debate with {num_participants} AI models.

YOUR ASSIGNED ROLE: {role}
CURRENT ROUND: OPENING STATEMENTS

This is the OPENING round. Your task:
1. Present your strongest case {role} the proposition
2. Do NOT rebut the other side yet - focus on YOUR arguments
3. Be clear, structured, and persuasive
4. You MUST argue {role}, regardless of your personal opinion

ALL INITIAL POSITIONS:
{all_initial_answers}

CRITIQUES RAISED:
{all_critiques}

Present your opening statement {role} the proposition."""

OXFORD_PROMPT_REBUTTAL = """{language_instruction}

You are in a formal Oxford-style debate with {num_participants} AI models.

YOUR ASSIGNED ROLE: {role}
CURRENT ROUND: REBUTTALS

This is the REBUTTAL round. Your task:
1. Address specific points made by the {opposing_role} side
2. Defend your position against their critiques
3. Reference opponents BY NAME (e.g., "Claude's argument that X fails because...")
4. Strengthen your case while weakening theirs

DISCUSSION SO FAR:
{discussion_history}

Deliver your rebuttal. Attack their weakest points, defend your strongest."""

OXFORD_PROMPT_CLOSING = """{language_instruction}

You are in a formal Oxford-style debate with {num_participants} AI models.

YOUR ASSIGNED ROLE: {role}
CURRENT ROUND: CLOSING STATEMENTS

This is the CLOSING round. Your task:
1. Summarize your strongest arguments
2. Explain why your side should win
3. This is your FINAL statement - make it count
4. Do NOT introduce new arguments - synthesize what was said

FULL DEBATE:
{discussion_history}

Deliver your closing statement. Why should {role} prevail?"""


def get_oxford_prompt(
    round_type: str,
    role: str,
    num_participants: int,
    all_initial_answers: str,
    all_critiques: str,
    discussion_history: str,
) -> str:
    """Get the appropriate Oxford debate prompt for the current round.

    Args:
        round_type: "opening", "rebuttal", or "closing"
        role: "FOR" or "AGAINST"
        num_participants: Number of participants
        all_initial_answers: Formatted initial answers
        all_critiques: Formatted critiques
        discussion_history: Discussion so far

    Returns:
        Formatted prompt for this round
    """
    opposing_role = "AGAINST" if role == "FOR" else "FOR"
    base_args = {
        "language_instruction": get_language_instruction(),
        "num_participants": num_participants,
        "role": role,
        "opposing_role": opposing_role,
        "all_initial_answers": all_initial_answers,
        "all_critiques": all_critiques,
        "discussion_history": discussion_history,
    }

    if round_type == "opening":
        return OXFORD_PROMPT_OPENING.format(**base_args)
    elif round_type == "rebuttal":
        return OXFORD_PROMPT_REBUTTAL.format(**base_args)
    else:  # closing
        return OXFORD_PROMPT_CLOSING.format(**base_args)


# --- ADVOCATE: Authentic Advocatus Diaboli (Cross-Examination) ---
#
# Based on the Catholic Church's "Promoter of the Faith" who examined
# candidates for sainthood. The advocate's role is to:
# 1. Examine specific claims and evidence systematically
# 2. Test the quality of reasoning through direct questioning
# 3. Identify weaknesses, not to "win" but to strengthen the final position
# 4. Deliver a verdict on what survived scrutiny

ADVOCATE_PROMPT_EXAMINER = """{language_instruction}

You are the ADVOCATUS DIABOLI (Devil's Advocate) conducting a cross-examination.

YOUR ROLE: Systematically examine the claims and reasoning of the defenders.
YOU ARE NOW EXAMINING: {target_name}

EXAMINATION ROUND: {current_round} of {total_rounds}

DISCUSSION SO FAR:
{discussion_history}

YOUR TASK:
1. Identify a SPECIFIC claim or piece of reasoning from {target_name}
2. Ask ONE focused question that tests:
   - The evidence supporting their claim
   - The logical consistency of their reasoning
   - Unstated assumptions they are making
   - Edge cases or counterexamples

EXAMINATION TECHNIQUES:
- "You claim X, but what evidence supports this?"
- "If X is true, how do you explain Y?"
- "What assumptions are you making when you say...?"
- "Have you considered the case where...?"

Address {target_name} DIRECTLY. Ask ONE clear, probing question.

If you believe {target_name}'s position has been thoroughly examined, you may state:
"EXAMINATION COMPLETE for {target_name}" and briefly note your assessment."""

ADVOCATE_PROMPT_EXAMINED = """{language_instruction}

You are being cross-examined by the Devil's Advocate (Advocatus Diaboli).

YOUR ROLE: Defend your position under direct examination.

DISCUSSION SO FAR:
{discussion_history}

YOU MUST:
1. Answer the specific question asked - do not evade
2. Provide evidence or reasoning to support your answer
3. If you cannot defend a point, acknowledge the weakness honestly
4. If the question reveals a flaw in your thinking, adapt your position

IMPORTANT: Start your response directly with your answer. Do NOT include role prefixes like "[DEFENDER]" or your model name - the system handles attribution automatically.

Remember: The advocate's job is to stress-test your reasoning.
Honest engagement strengthens the final outcome."""

ADVOCATE_PROMPT_VERDICT = """{language_instruction}

You are the ADVOCATUS DIABOLI. The cross-examination is complete.

FULL EXAMINATION TRANSCRIPT:
{discussion_history}

Deliver your VERDICT. You must assess:

1. CLAIMS THAT SURVIVED SCRUTINY
   - Which positions held up under examination?
   - What evidence proved compelling?

2. CLAIMS THAT FAILED OR WEAKENED
   - Which arguments could not be adequately defended?
   - What logical flaws or gaps were exposed?

3. UNRESOLVED QUESTIONS
   - What important questions remain unanswered?
   - What would need further investigation?

4. OVERALL ASSESSMENT
   - Is the defenders' collective position sound?
   - What is the quality of their reasoning?

Be fair and objective. Your role was to test, not to win."""


def get_advocate_examiner_prompt(
    target_name: str,
    discussion_history: str,
    current_round: int = 1,
    total_rounds: int = 1,
) -> str:
    """Get prompt for the devil's advocate examining a specific defender.

    Args:
        target_name: Name of the defender being examined
        discussion_history: Discussion so far
        current_round: Current examination round (1-indexed)
        total_rounds: Total number of examination rounds

    Returns:
        Formatted prompt for cross-examination
    """
    return ADVOCATE_PROMPT_EXAMINER.format(
        language_instruction=get_language_instruction(),
        target_name=target_name,
        discussion_history=discussion_history,
        current_round=current_round,
        total_rounds=total_rounds,
    )


def get_advocate_examined_prompt(discussion_history: str) -> str:
    """Get prompt for a defender being cross-examined.

    Args:
        discussion_history: Discussion so far

    Returns:
        Formatted prompt for the examined defender
    """
    return ADVOCATE_PROMPT_EXAMINED.format(
        language_instruction=get_language_instruction(),
        discussion_history=discussion_history,
    )


def get_advocate_verdict_prompt(discussion_history: str) -> str:
    """Get prompt for the advocate's final verdict.

    Args:
        discussion_history: Full examination transcript

    Returns:
        Formatted prompt for verdict
    """
    return ADVOCATE_PROMPT_VERDICT.format(
        language_instruction=get_language_instruction(),
        discussion_history=discussion_history,
    )


# --- SOCRATIC: Rotating questioner/respondent ---

SOCRATIC_PROMPT_QUESTIONER = """{language_instruction}

You are engaging in authentic Socratic dialogue, examining a thesis through critical questioning.

DIALOGUE PROGRESS: Round {current_round} of {total_rounds}
{round_guidance}

YOUR ROLE: QUESTIONER (like Socrates)
YOU ARE EXAMINING: {respondent_name}

You must ask ONE probing question directed at {respondent_name} that:
1. Targets a specific claim or assumption from their responses
2. Exposes unclear reasoning or hidden assumptions
3. Deepens understanding rather than attacking

IMPORTANT: Address your question directly to {respondent_name}. They are the thesis presenter being examined.

DO NOT:
- State your own opinion
- Answer your own question
- Ask multiple questions
- Ask vague or rhetorical questions

THE THESIS BEING EXAMINED:
{all_initial_answers}

DIALOGUE SO FAR:
{discussion_history}

Ask ONE thought-provoking question to {respondent_name}.
"""

SOCRATIC_PROMPT_RESPONDENT = """{language_instruction}

You are engaging in Socratic dialogue with {num_participants} AI models.

DIALOGUE PROGRESS: Round {current_round} of {total_rounds}
{round_guidance}

YOUR ROLE THIS TURN: RESPONDENT

The Questioner has asked:
"{question}"

Your task:
1. Answer the question directly and thoroughly
2. Explain your reasoning step by step
3. Acknowledge uncertainty where it exists
4. If the question reveals a flaw in your thinking, admit it honestly
5. Be concise but complete

CONTEXT FROM INITIAL ANSWERS:
{all_initial_answers}

DISCUSSION SO FAR:
{discussion_history}

Respond directly to the question asked."""


def _get_socratic_round_guidance(current_round: int, total_rounds: int) -> str:
    """Get contextual guidance for Socratic rounds."""
    remaining = total_rounds - current_round

    if current_round == 1:
        return "→ Opening round: Ask about the most fundamental assumption."
    elif remaining == 0:
        return "→ FINAL ROUND: Ask the most important remaining question."
    elif current_round == 2:
        return "→ Second round: Dig deeper into emerging themes."
    else:
        return "→ Continue exploring: Build on insights from previous rounds."


def get_socratic_questioner_prompt(
    num_participants: int,
    all_initial_answers: str,
    discussion_history: str,
    respondent_name: str,
    current_round: int = 1,
    total_rounds: int = 1,
) -> str:
    """Get prompt for the Socratic questioner.

    Args:
        num_participants: Number of participants
        all_initial_answers: The thesis being examined
        discussion_history: Discussion so far
        respondent_name: Name of the model being questioned (thesis presenter)
        current_round: Current round number (1-indexed)
        total_rounds: Total number of rounds

    Returns:
        Formatted prompt for questioner
    """
    round_guidance = _get_socratic_round_guidance(current_round, total_rounds)

    return SOCRATIC_PROMPT_QUESTIONER.format(
        language_instruction=get_language_instruction(),
        num_participants=num_participants,
        all_initial_answers=all_initial_answers,
        discussion_history=discussion_history,
        respondent_name=respondent_name,
        current_round=current_round,
        total_rounds=total_rounds,
        round_guidance=round_guidance,
    )


def get_socratic_respondent_prompt(
    num_participants: int,
    all_initial_answers: str,
    question: str,
    discussion_history: str,
    current_round: int = 1,
    total_rounds: int = 1,
) -> str:
    """Get prompt for Socratic respondents.

    Args:
        num_participants: Number of participants
        all_initial_answers: Formatted initial answers
        question: The question asked by the questioner
        discussion_history: Discussion so far
        current_round: Current round number (1-indexed)
        total_rounds: Total number of rounds

    Returns:
        Formatted prompt for respondent
    """
    round_guidance = _get_socratic_round_guidance(current_round, total_rounds)

    return SOCRATIC_PROMPT_RESPONDENT.format(
        language_instruction=get_language_instruction(),
        num_participants=num_participants,
        all_initial_answers=all_initial_answers,
        question=question,
        discussion_history=discussion_history,
        current_round=current_round,
        total_rounds=total_rounds,
        round_guidance=round_guidance,
    )


# --- STANDARD: Kept for direct agent creation ---

def _get_turn_guidance(current_turn: int, total_turns: int) -> str:
    """Get contextual guidance based on turn position."""
    remaining = total_turns - current_turn

    if current_turn == 1:
        return "→ Opening turn: Set the direction for the discussion."
    elif remaining == 0:
        return "→ FINAL TURN: This is your last chance to contribute. Make it count!"
    elif remaining == 1:
        return "→ Second-to-last turn: Start wrapping up your key points."
    elif current_turn <= total_turns // 3:
        return "→ Early discussion: Focus on key disagreements and missing points."
    elif current_turn <= 2 * total_turns // 3:
        return "→ Mid-discussion: Build toward synthesis and common ground."
    else:
        return "→ Late discussion: Focus on reaching consensus."


def get_standard_discussion_prompt(
    num_participants: int,
    your_initial_answer: str,
    all_initial_answers: str,
    all_critiques: str,
    current_turn: int = 1,
    total_turns: int = 1,
    discussion_history: str = "",
) -> str:
    """Get standard discussion prompt (Phase 3).

    Args:
        num_participants: Number of participants
        your_initial_answer: This agent's initial answer
        all_initial_answers: Formatted initial answers
        all_critiques: Formatted critiques
        current_turn: Current turn number (1-indexed)
        total_turns: Total number of turns
        discussion_history: Previous discussion messages

    Returns:
        Formatted standard discussion prompt
    """
    turn_guidance = _get_turn_guidance(current_turn, total_turns)

    discussion_history_section = ""
    if discussion_history:
        discussion_history_section = f"DISCUSSION SO FAR:\n{discussion_history}"

    return DISCUSSION_PROMPT_STANDARD.format(
        language_instruction=get_language_instruction(),
        num_participants=num_participants,
        your_initial_answer=your_initial_answer,
        all_initial_answers=all_initial_answers,
        all_critiques=all_critiques,
        current_turn=current_turn,
        total_turns=total_turns,
        turn_guidance=turn_guidance,
        discussion_history_section=discussion_history_section,
    )


# =============================================================================
# PHASE 4: Final position prompt (with confidence)
# =============================================================================
FINAL_POSITION_PROMPT = """{language_instruction}

The AI-to-AI discussion is now complete.

ORIGINAL QUESTION:
{original_question}

State YOUR final position after considering all perspectives.

IMPORTANT:
- State your position only - do NOT ask for user input
- Do NOT end with "let me know if you want more details"
- This is your FINAL conclusion

Format EXACTLY as:
POSITION: [your final answer - be concise]
CONFIDENCE: [HIGH/MEDIUM/LOW]

Where:
- HIGH = Very certain, strong agreement among models
- MEDIUM = Reasonably confident but some uncertainty
- LOW = Uncertain, valid arguments on multiple sides"""


# =============================================================================
# PHASE 5: Synthesis prompt (one model synthesizes all final positions)
# =============================================================================
SYNTHESIS_PROMPT = """{language_instruction}

You are synthesizing the results of an AI-to-AI discussion.

THE ORIGINAL QUESTION:
{original_question}

FINAL POSITIONS FROM ALL {num_participants} MODELS:
{all_positions}

Your task:
1. Determine if there is consensus among the models
2. Write a comprehensive synthesized answer using proper markdown formatting
3. Note any significant differences between positions

Format your response EXACTLY as:
CONSENSUS: [YES/PARTIAL/NO]
SYNTHESIS: [Write a well-structured answer using markdown:
- Use ## headers for main sections
- Use **bold** for key points
- Use bullet points for lists
- Be thorough but concise]
DIFFERENCES: [Any notable disagreements or nuance differences, or "None" if full consensus]

Guidelines:
- YES = All models fundamentally agree on the core answer
- PARTIAL = Models agree on main points but differ on details or emphasis
- NO = Models have substantially different positions

Be objective and accurate in your assessment."""




def _make_valid_identifier(s: str) -> str:
    """Convert a string to a valid Python identifier."""
    import re
    # Replace invalid characters with underscores
    result = re.sub(r'[^a-zA-Z0-9_]', '_', s)
    # Ensure it doesn't start with a number
    if result and result[0].isdigit():
        result = '_' + result
    return result


def get_phase1_prompt(num_participants: int) -> str:
    """Get the Phase 1 (independent answer) prompt.

    Args:
        num_participants: Number of participants in the discussion.

    Returns:
        Formatted Phase 1 system prompt.
    """
    return PHASE1_PROMPT.format(
        language_instruction=get_language_instruction(),
        num_participants=num_participants,
        markdown_instruction=MARKDOWN_INSTRUCTION,
    )


def get_critique_prompt(
    num_participants: int,
    your_initial_answer: str,
    all_initial_answers: str,
) -> str:
    """Get the critique prompt (Phase 2 in new system).

    Args:
        num_participants: Number of participants.
        your_initial_answer: This agent's Phase 1 answer.
        all_initial_answers: Formatted string of all initial answers.

    Returns:
        Formatted critique prompt.
    """
    return CRITIQUE_PROMPT.format(
        language_instruction=get_language_instruction(),
        num_participants=num_participants,
        your_initial_answer=your_initial_answer,
        all_initial_answers=all_initial_answers,
    )


def get_final_position_prompt(original_question: str) -> str:
    """Get the final position prompt (Phase 4).

    Args:
        original_question: The original question being discussed.

    Returns:
        Formatted final position prompt.
    """
    return FINAL_POSITION_PROMPT.format(
        language_instruction=get_language_instruction(),
        original_question=original_question,
    )


def get_synthesis_prompt(
    original_question: str,
    num_participants: int,
    all_positions: str,
) -> str:
    """Get the synthesis prompt (Phase 5).

    Args:
        original_question: The original question being discussed.
        num_participants: Number of participants.
        all_positions: Formatted string of all final positions.

    Returns:
        Formatted synthesis prompt.
    """
    return SYNTHESIS_PROMPT.format(
        language_instruction=get_language_instruction(),
        original_question=original_question,
        num_participants=num_participants,
        all_positions=all_positions,
    )


# =============================================================================
# DELPHI METHOD: Iterative consensus for estimates and forecasts
# =============================================================================
# Based on RAND Corporation methodology (1950s-60s)
# Key principles: Anonymity, iterative rounds, controlled feedback, convergence
# Source: https://en.wikipedia.org/wiki/Delphi_method

DELPHI_PROMPT_ROUND1 = """{language_instruction}

You are participating in a DELPHI consensus process with {num_participants} AI models.

PHASE: ROUND 1 - INDEPENDENT ESTIMATES
Your estimate will be shared ANONYMOUSLY. Other panelists cannot see who gave which estimate.

THE QUESTION:
{question}

PROVIDE YOUR RESPONSE IN THIS EXACT FORMAT:

ESTIMATE: [Your specific estimate - be quantitative where possible: numbers, ranges, probabilities, timeframes]

CONFIDENCE: [HIGH / MEDIUM / LOW]
- HIGH = Very certain, strong evidence base
- MEDIUM = Reasonably confident, some assumptions
- LOW = Uncertain, limited data or many variables

KEY ASSUMPTIONS:
- [List 2-4 critical assumptions underlying your estimate]

REASONING:
[Brief justification for your estimate - what evidence or logic supports it?]

Be specific and quantitative. Avoid vague answers like "it depends" - commit to an estimate."""

DELPHI_PROMPT_REVISION = """{language_instruction}

You are participating in a DELPHI consensus process with {num_participants} AI models.

PHASE: ROUND {round_number} - INFORMED REVISION
Review the anonymous group estimates and revise your position if warranted.

YOUR PREVIOUS ESTIMATE:
{your_previous_estimate}

ANONYMOUS GROUP ESTIMATES (Round {previous_round}):
{group_estimates}

GROUP STATISTICS:
{group_statistics}

YOUR TASK:
1. Consider the range of estimates from other panelists
2. Evaluate whether their reasoning reveals factors you missed
3. Revise your estimate if the evidence warrants it (or maintain if still confident)

RESPOND IN THIS EXACT FORMAT:

REVISED ESTIMATE: [Your updated estimate, or "UNCHANGED: [original]" if maintaining]

CONFIDENCE: [HIGH / MEDIUM / LOW]

REVISION RATIONALE:
[If changed: What new consideration influenced you?]
[If unchanged: Why do you maintain your original position despite other estimates?]

KEY ASSUMPTIONS:
- [Updated list if changed]

Note: It is intellectually honest to revise based on good arguments. It is also valid to maintain your position if you have strong reasons."""

DELPHI_PROMPT_SYNTHESIS = """{language_instruction}

You are synthesizing the results of a DELPHI consensus process.

THE ORIGINAL QUESTION:
{question}

FINAL ROUND ESTIMATES FROM ALL {num_participants} PANELISTS:
{final_estimates}

ESTIMATE EVOLUTION:
{estimate_history}

YOUR TASK - Produce an AGGREGATED ESTIMATE:

1. CONVERGENCE ASSESSMENT
   - Did estimates converge over rounds? (YES/PARTIAL/NO)
   - What is the current spread/range?

2. AGGREGATED ESTIMATE
   - Synthesize a final group estimate
   - Weight by confidence levels where appropriate
   - Provide a central estimate and reasonable range

3. KEY FACTORS
   - What assumptions were most commonly shared?
   - What reasoning proved most compelling?

4. OUTLIER PERSPECTIVES
   - Note any significantly different estimates
   - Explain why they may still have merit

Format your response as:
CONVERGENCE: [YES/PARTIAL/NO]
AGGREGATED ESTIMATE: [The group's synthesized estimate with confidence range]
KEY FACTORS: [Shared assumptions and compelling reasoning]
OUTLIER PERSPECTIVES: [Dissenting views worth noting, or "None - strong convergence"]"""


def get_delphi_round1_prompt(num_participants: int, question: str) -> str:
    """Get Delphi Round 1 prompt for independent estimates."""
    return DELPHI_PROMPT_ROUND1.format(
        language_instruction=get_language_instruction(),
        num_participants=num_participants,
        question=question,
    )


def get_delphi_revision_prompt(
    num_participants: int,
    round_number: int,
    your_previous_estimate: str,
    group_estimates: str,
    group_statistics: str,
) -> str:
    """Get Delphi revision prompt for subsequent rounds."""
    return DELPHI_PROMPT_REVISION.format(
        language_instruction=get_language_instruction(),
        num_participants=num_participants,
        round_number=round_number,
        previous_round=round_number - 1,
        your_previous_estimate=your_previous_estimate,
        group_estimates=group_estimates,
        group_statistics=group_statistics,
    )


def get_delphi_synthesis_prompt(
    question: str,
    num_participants: int,
    final_estimates: str,
    estimate_history: str,
) -> str:
    """Get Delphi synthesis prompt for final aggregation."""
    return DELPHI_PROMPT_SYNTHESIS.format(
        language_instruction=get_language_instruction(),
        question=question,
        num_participants=num_participants,
        final_estimates=final_estimates,
        estimate_history=estimate_history,
    )


# =============================================================================
# BRAINSTORM METHOD: Divergent → Convergent creative ideation
# =============================================================================
# Based on Alex Osborn's methodology (1953, "Applied Imagination")
# Osborn's 4 rules: Defer judgment, wild ideas, quantity, build on others
# Source: Creative Education Foundation

BRAINSTORM_PROMPT_DIVERGE = """{language_instruction}

You are brainstorming with {num_participants} AI models.

PHASE 1 - DIVERGE: Generate Wild Ideas

OSBORN'S BRAINSTORMING RULES (YOU MUST FOLLOW):
1. DEFER JUDGMENT - Do NOT evaluate or criticize ideas (yours or others')
2. WILD IDEAS WELCOME - The crazier the better; wild ideas spark practical ones
3. QUANTITY OVER QUALITY - Generate as many ideas as possible
4. BUILD ON IDEAS - Combine and expand (that comes in Phase 2)

THE CHALLENGE:
{question}

YOUR TASK:
Generate at least 5 DISTINCT ideas. Number them clearly.

FORMAT:
1. [First idea - one sentence description]
2. [Second idea]
3. [Third idea]
4. [Fourth idea]
5. [Fifth idea]
[Continue if you have more...]

REMEMBER:
- NO evaluation or criticism ("this might not work" = FORBIDDEN)
- NO filtering ("this is silly but..." = FORBIDDEN)
- Push beyond obvious answers
- Weird, unconventional, ambitious ideas are encouraged
- You will evaluate feasibility LATER - not now"""

BRAINSTORM_PROMPT_BUILD = """{language_instruction}

You are brainstorming with {num_participants} AI models.

PHASE 2 - BUILD: Combine & Expand

ALL IDEAS GENERATED IN PHASE 1:
{all_ideas}

YOUR TASK:
Build on the most promising ideas from ALL models (not just yours).

TECHNIQUES:
1. COMBINE - Merge two or more ideas into something new
2. EXPAND - Take an idea further, add detail, scale it up
3. PIVOT - Use one idea as a springboard for a related but different idea
4. ADAPT - Modify an idea to work in a different context

FORMAT YOUR RESPONSE:
BUILDING ON [Model name]'s idea #[X]:
[Your expanded/combined idea]

COMBINING [Model A]'s #[X] + [Model B]'s #[Y]:
[The combined idea]

[Continue with 3-5 build-ons...]

STILL NO JUDGMENT - Continue generating, not evaluating.
Reference specific ideas by model name and number."""

BRAINSTORM_PROMPT_CONVERGE = """{language_instruction}

You are brainstorming with {num_participants} AI models.

PHASE 3 - CONVERGE: Select & Refine

ALL IDEAS AND BUILD-ONS:
{all_ideas_and_builds}

YOUR TASK:
Now you MAY evaluate. Select the TOP 3 ideas that best address the original challenge.

FOR EACH SELECTION:
1. IDEA: [State the idea clearly]
2. WHY IT'S PROMISING: [Key strengths]
3. REFINEMENT: [How to make it even better or more practical]
4. QUICK WIN OR BIG BET: [Is this easy to implement or ambitious?]

FORMAT:
TOP PICK #1:
IDEA: [The idea]
SOURCE: [Which model(s) contributed]
WHY: [Why this is promising]
REFINEMENT: [How to improve]
TYPE: [Quick Win / Big Bet]

TOP PICK #2:
[Same format...]

TOP PICK #3:
[Same format...]

Justify your selections. Focus on ideas that are NOVEL + ACTIONABLE."""


def get_brainstorm_diverge_prompt(num_participants: int, question: str) -> str:
    """Get Brainstorm Phase 1 (Diverge) prompt."""
    return BRAINSTORM_PROMPT_DIVERGE.format(
        language_instruction=get_language_instruction(),
        num_participants=num_participants,
        question=question,
    )


def get_brainstorm_build_prompt(num_participants: int, all_ideas: str) -> str:
    """Get Brainstorm Phase 2 (Build) prompt."""
    return BRAINSTORM_PROMPT_BUILD.format(
        language_instruction=get_language_instruction(),
        num_participants=num_participants,
        all_ideas=all_ideas,
    )


def get_brainstorm_converge_prompt(num_participants: int, all_ideas_and_builds: str) -> str:
    """Get Brainstorm Phase 3 (Converge) prompt."""
    return BRAINSTORM_PROMPT_CONVERGE.format(
        language_instruction=get_language_instruction(),
        num_participants=num_participants,
        all_ideas_and_builds=all_ideas_and_builds,
    )


BRAINSTORM_SYNTHESIS_PROMPT = """{language_instruction}

You are synthesizing the results of a creative brainstorming session.

THE ORIGINAL CHALLENGE:
{question}

ALL SELECTIONS FROM {num_participants} MODELS:
{all_selections}

YOUR TASK - Produce the FINAL SELECTED IDEAS:

1. Identify which ideas received the most nominations
2. Synthesize overlapping selections into refined versions
3. Present the top ideas with actionable next steps

FORMAT:
SELECTED IDEAS: [Total count of finalist ideas]

IDEA 1: [Title]
DESCRIPTION: [Clear explanation]
CONTRIBUTED BY: [Model names]
NEXT STEPS: [How to pursue this]

IDEA 2: [Title]
[Same format...]

ALTERNATIVE DIRECTIONS:
[Note any promising ideas that didn't make the top list but deserve consideration]"""


def get_brainstorm_synthesis_prompt(
    question: str,
    num_participants: int,
    all_selections: str,
) -> str:
    """Get Brainstorm synthesis prompt."""
    return BRAINSTORM_SYNTHESIS_PROMPT.format(
        language_instruction=get_language_instruction(),
        question=question,
        num_participants=num_participants,
        all_selections=all_selections,
    )


# =============================================================================
# TRADEOFF METHOD: Structured multi-criteria decision analysis
# =============================================================================
# Based on MCDA (Multi-Criteria Decision Analysis)
# Key concept: Neutral evaluators score alternatives against defined criteria
# Source: https://en.wikipedia.org/wiki/Multiple-criteria_decision_analysis

TRADEOFF_PROMPT_FRAME = """{language_instruction}

You are conducting a STRUCTURED TRADEOFF ANALYSIS with {num_participants} AI models.

PHASE 1 - FRAME: Define the Alternatives

THE DECISION:
{question}

YOUR TASK:
Identify 2-4 distinct ALTERNATIVES to compare.

RULES:
- Alternatives must be mutually exclusive (can't do both)
- Each must be a viable option
- Include the "do nothing" or "status quo" option if relevant
- Be specific, not vague

FORMAT:
ALTERNATIVE A: [Name]
DESCRIPTION: [1-2 sentences explaining this option]

ALTERNATIVE B: [Name]
DESCRIPTION: [1-2 sentences]

ALTERNATIVE C: [Name] (if applicable)
DESCRIPTION: [1-2 sentences]

[Maximum 4 alternatives]

Focus on the most distinct, viable options. Avoid overlapping alternatives."""

TRADEOFF_PROMPT_CRITERIA = """{language_instruction}

You are conducting a STRUCTURED TRADEOFF ANALYSIS with {num_participants} AI models.

PHASE 2 - CRITERIA: Establish Evaluation Dimensions

ALTERNATIVES IDENTIFIED:
{alternatives}

YOUR TASK:
Define 4-6 CRITERIA for evaluating these alternatives.

GOOD CRITERIA ARE:
- Relevant to the decision
- Measurable or at least comparable
- Distinct (not overlapping with other criteria)
- Important to the decision-maker

SUGGESTED CATEGORIES:
- Cost / Resources required
- Effectiveness / Impact
- Risk / Downside
- Time / Speed
- Feasibility / Complexity
- Strategic fit / Alignment

FORMAT:
CRITERION 1: [Name]
DEFINITION: [What this measures]
WHY IT MATTERS: [Brief justification]

CRITERION 2: [Name]
[Same format...]

[4-6 criteria total]

These criteria will be used to score each alternative in the next phase."""

TRADEOFF_PROMPT_EVALUATE = """{language_instruction}

You are conducting a STRUCTURED TRADEOFF ANALYSIS with {num_participants} AI models.

PHASE 3 - EVALUATE: Score Each Option

ALTERNATIVES:
{alternatives}

EVALUATION CRITERIA:
{criteria}

YOUR TASK:
Score each alternative on each criterion using a 1-10 scale.
- 1-3: Poor (significant weaknesses)
- 4-6: Moderate (acceptable, some concerns)
- 7-10: Strong (clear advantages)

FORMAT YOUR EVALUATION AS A TABLE:

| Criterion | {alternative_headers} |
|-----------|{header_dashes}|
| [Criterion 1] | [Score A] | [Score B] | ... |
| [Criterion 2] | [Score A] | [Score B] | ... |
| ... | ... | ... | ... |
| **TOTAL** | [Sum A] | [Sum B] | ... |

EVALUATION NOTES:
[For each alternative, explain your most significant scoring decision - what drove your highest and lowest scores]

KEY TRADEOFF:
[Identify the most important tradeoff: "A is better for X, but B is better for Y"]

Be objective. Your role is to evaluate neutrally, not to advocate."""

TRADEOFF_PROMPT_DECIDE = """{language_instruction}

You are synthesizing a STRUCTURED TRADEOFF ANALYSIS.

THE ORIGINAL DECISION:
{question}

ALTERNATIVES:
{alternatives}

CRITERIA:
{criteria}

ALL EVALUATIONS FROM {num_participants} MODELS:
{all_evaluations}

YOUR TASK - Produce a RECOMMENDATION:

1. AGGREGATE SCORES
   - Average the scores from all evaluators
   - Identify which alternative "wins" on raw totals

2. AGREEMENT ASSESSMENT
   - Do evaluators agree on the recommendation? (YES/NO)
   - Where do they disagree most?

3. TRADEOFF ANALYSIS
   - What is the key tradeoff between the top options?
   - Under what conditions would a different choice be better?

4. RECOMMENDATION
   - State the recommended alternative
   - Explain the key reasons
   - Note important caveats

FORMAT:
AGREEMENT: [YES - all agree / NO - split decision]
RECOMMENDATION: [Alternative name]

AGGREGATED SCORES:
| Alternative | Average Score | Evaluator Agreement |
|-------------|--------------|---------------------|
| [Alt A] | [X.X] | [# of evaluators who ranked it first] |
| [Alt B] | [X.X] | [#] |
...

KEY TRADEOFFS:
[The most important tradeoffs to consider]

ANALYSIS:
[Clear explanation of why the recommendation makes sense]

WHEN TO CHOOSE DIFFERENTLY:
[Conditions under which another alternative would be better]"""


def get_tradeoff_frame_prompt(num_participants: int, question: str) -> str:
    """Get Tradeoff Phase 1 (Frame) prompt."""
    return TRADEOFF_PROMPT_FRAME.format(
        language_instruction=get_language_instruction(),
        num_participants=num_participants,
        question=question,
    )


def get_tradeoff_criteria_prompt(num_participants: int, alternatives: str) -> str:
    """Get Tradeoff Phase 2 (Criteria) prompt."""
    return TRADEOFF_PROMPT_CRITERIA.format(
        language_instruction=get_language_instruction(),
        num_participants=num_participants,
        alternatives=alternatives,
    )


def get_tradeoff_evaluate_prompt(
    num_participants: int,
    alternatives: str,
    criteria: str,
    alternative_names: list[str],
) -> str:
    """Get Tradeoff Phase 3 (Evaluate) prompt."""
    alternative_headers = " | ".join(alternative_names)
    header_dashes = " | ".join(["---"] * len(alternative_names))

    return TRADEOFF_PROMPT_EVALUATE.format(
        language_instruction=get_language_instruction(),
        num_participants=num_participants,
        alternatives=alternatives,
        criteria=criteria,
        alternative_headers=alternative_headers,
        header_dashes=header_dashes,
    )


def get_tradeoff_decide_prompt(
    question: str,
    num_participants: int,
    alternatives: str,
    criteria: str,
    all_evaluations: str,
) -> str:
    """Get Tradeoff Phase 4 (Decide) synthesis prompt."""
    return TRADEOFF_PROMPT_DECIDE.format(
        language_instruction=get_language_instruction(),
        question=question,
        num_participants=num_participants,
        alternatives=alternatives,
        criteria=criteria,
        all_evaluations=all_evaluations,
    )


# =============================================================================
# Method Advisor - Recommends best discussion method for a question
# =============================================================================

METHOD_ADVISOR_PROMPT = """{language_instruction}

You are a Method Advisor for a multi-AI discussion system.

Your task: Analyze the user's question and recommend the BEST discussion method.

AVAILABLE METHODS:

1. STANDARD - Balanced 5-phase discussion
   Best for: General questions, balanced analysis, when no specialized method fits
   Phases: Answer → Critique → Discuss → Position → Synthesis

2. OXFORD - Formal debate with FOR/AGAINST teams
   Best for: Controversial topics, "should we" questions, policy debates
   Requires: EVEN number of models (2, 4, 6...)
   Phases: Opening → Rebuttal → Closing → Judgement

3. ADVOCATE - Devil's advocate challenges the group
   Best for: Risk analysis, finding flaws, stress-testing ideas
   Requires: 3+ models
   Phases: Initial Position → Cross-Examination → Verdict

4. SOCRATIC - Deep inquiry through questioning
   Best for: Deep understanding, "why" questions, exploring fundamentals
   Phases: Thesis → Inquiry → Aporia

5. DELPHI - Iterative consensus for estimates
   Best for: Forecasts, time estimates, cost projections, quantitative predictions
   Requires: 3+ models
   Phases: Round 1 → Round 2 → Round 3 (adaptive) → Aggregation

6. BRAINSTORM - Creative ideation
   Best for: Generating ideas, creative solutions, "how might we" questions
   Phases: Diverge (wild ideas) → Build → Converge → Synthesis

7. TRADEOFF - Structured comparison of alternatives
   Best for: "A vs B" decisions, comparing options, multi-criteria analysis
   Phases: Frame → Criteria → Evaluate → Decide

QUESTION TO ANALYZE:
{question}

OUTPUT FORMAT (strict JSON):
{{
  "primary": {{
    "method": "METHOD_NAME_LOWERCASE",
    "confidence": 0-100,
    "reason": "Brief explanation why this is the best fit"
  }},
  "alternatives": [
    {{"method": "METHOD_NAME_LOWERCASE", "confidence": 0-100, "reason": "Why this could also work"}}
  ]
}}

RULES:
- Be decisive. The primary should clearly be the best fit.
- Include 1-2 alternatives at most.
- Confidence for primary should be 70+ if it's a good fit.
- Method names must be lowercase: standard, oxford, advocate, socratic, delphi, brainstorm, tradeoff

Respond with ONLY the JSON, no other text."""


def get_method_advisor_prompt(question: str) -> str:
    """Get prompt for method advisor to analyze a question."""
    return METHOD_ADVISOR_PROMPT.format(
        language_instruction=get_language_instruction(),
        question=question
    )
