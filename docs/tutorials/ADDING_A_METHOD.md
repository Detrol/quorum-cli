# Adding a New Discussion Method

This tutorial walks through adding a new discussion method to Quorum. We'll use a hypothetical "Consensus Ladder" method as an example.

## Overview

Adding a method requires changes to:

1. **`agents.py`** - Prompt templates and validation
2. **`team.py`** - Orchestration flow
3. **`ipc.py`** - Method validation list
4. **Frontend** - TypeScript types and UI
5. **Tests** - Method flow tests
6. **Docs** - README and help

## Step 1: Define the Method

First, define your method's structure:

| Aspect | Decision |
|--------|----------|
| **Name** | `ladder` |
| **Phases** | 3 (Propose → Rank → Climb) |
| **Model requirement** | 3+ models |
| **Roles** | None (all equal) |
| **Special behavior** | Iterative elimination of weakest ideas |

## Step 2: Add Prompts (`agents.py`)

### 2.1 Add Phase Prompts

```python
# =============================================================================
# Ladder Method - Iterative idea elimination
# =============================================================================

DISCUSSION_PROMPT_LADDER_PROPOSE = """{language_instruction}

You are an AI model in a Consensus Ladder discussion with {num_participants} models.

PHASE 1 - PROPOSE
Generate 3 distinct solutions to the question. Number them clearly:

1. [Solution A]: ...
2. [Solution B]: ...
3. [Solution C]: ...

For each solution, briefly explain:
- Key approach
- Main advantage
- Potential weakness

Be creative and diverse in your proposals."""


DISCUSSION_PROMPT_LADDER_RANK = """{language_instruction}

You are ranking proposals in a Consensus Ladder discussion.

ALL PROPOSALS:
{all_initial_answers}

PHASE 2 - RANK
Review all proposals and rank the TOP 3 ideas overall (across all models).

Format:
RANK 1: [Model] Solution [X] - [Brief reason]
RANK 2: [Model] Solution [X] - [Brief reason]
RANK 3: [Model] Solution [X] - [Brief reason]
ELIMINATE: [List ideas that should be dropped and why]

Be objective. The best ideas may not be your own."""


DISCUSSION_PROMPT_LADDER_CLIMB = """{language_instruction}

You are in the final climb phase of a Consensus Ladder discussion.

SURVIVING IDEAS (after elimination):
{discussion_history}

PHASE 3 - CLIMB
Take the top-ranked idea and IMPROVE it by:
1. Addressing any weaknesses identified
2. Incorporating strengths from eliminated ideas
3. Adding implementation details

Build on the collective work to create the strongest possible answer."""
```

### 2.2 Add Method Validation

In `agents.py`, find or create the validation function:

```python
METHOD_MODEL_REQUIREMENTS = {
    "standard": (2, None),  # min 2, no max
    "oxford": (2, None, "even"),  # min 2, no max, must be even
    "advocate": (3, None),  # min 3, no max
    "socratic": (2, None),
    "delphi": (3, None),
    "brainstorm": (2, None),
    "tradeoff": (2, None),
    "ladder": (3, None),  # ADD THIS
}


def validate_method_model_count(method: str, model_count: int) -> tuple[bool, str | None]:
    """Validate model count for method."""
    if method not in METHOD_MODEL_REQUIREMENTS:
        return False, f"Unknown method: {method}"

    min_count, max_count, *flags = METHOD_MODEL_REQUIREMENTS[method] + (None,)

    if model_count < min_count:
        return False, f"{method.title()} requires at least {min_count} models"

    if max_count and model_count > max_count:
        return False, f"{method.title()} allows at most {max_count} models"

    if "even" in (flags or []) and model_count % 2 != 0:
        return False, f"{method.title()} requires an even number of models"

    return True, None
```

### 2.3 Add Synthesis Prompt (if custom needed)

```python
SYNTHESIS_PROMPT_LADDER = """{language_instruction}

You are synthesizing the result of a Consensus Ladder discussion.

QUESTION: {question}

FINAL PROPOSAL (after ranking and climbing):
{discussion_history}

CONFIDENCE LEVELS:
{confidence_summary}

Create a synthesis that presents:
1. THE SOLUTION: The refined final answer
2. HOW IT EVOLVED: Brief summary of the ladder process
3. KEY TRADEOFFS: What was sacrificed for this solution

Format with CONSENSUS: [YES/PARTIAL/NO] at the start."""
```

## Step 3: Add Orchestration (`team.py`)

### 3.1 Add Flow Method

In `team.py`, find `FourPhaseConsensusTeam` and add:

```python
async def _run_ladder_flow(self, task: str):
    """Run Ladder method: Propose → Rank → Climb → Synthesize."""
    from .agents import (
        DISCUSSION_PROMPT_LADDER_PROPOSE,
        DISCUSSION_PROMPT_LADDER_RANK,
        DISCUSSION_PROMPT_LADDER_CLIMB,
    )

    # Phase 1: Propose
    yield PhaseMarker(
        phase=1,
        message="Phase 1: Propose Solutions",
        num_participants=len(self.model_ids),
        method="ladder",
        total_phases=3,
    )

    proposals = []
    # Run all models in parallel
    async def get_proposal(model_id):
        prompt = DISCUSSION_PROMPT_LADDER_PROPOSE.format(
            language_instruction=get_language_instruction(),
            num_participants=len(self.model_ids),
        )
        yield ThinkingIndicator(model=model_id)
        response = await self._call_model(model_id, task, prompt)
        return IndependentAnswer(source=model_id, content=response)

    for coro in asyncio.as_completed([get_proposal(m) for m in self.model_ids]):
        answer = await coro
        proposals.append(answer)
        yield answer

    # Phase 2: Rank
    yield PhaseMarker(
        phase=2,
        message="Phase 2: Rank and Eliminate",
        num_participants=len(self.model_ids),
        method="ladder",
        total_phases=3,
    )

    all_proposals = self._format_answers(proposals)
    rankings = []

    for model_id in self.model_ids:
        yield ThinkingIndicator(model=model_id)
        prompt = DISCUSSION_PROMPT_LADDER_RANK.format(
            language_instruction=get_language_instruction(),
            all_initial_answers=all_proposals,
        )
        response = await self._call_model(model_id, task, prompt)
        rankings.append(TeamTextMessage(
            source=model_id,
            content=response,
            method="ladder",
        ))
        yield rankings[-1]

    # Phase 3: Climb (refine top ideas)
    yield PhaseMarker(
        phase=3,
        message="Phase 3: Climb to Consensus",
        num_participants=len(self.model_ids),
        method="ladder",
        total_phases=3,
    )

    surviving_ideas = self._extract_top_ideas(rankings)  # Helper to parse rankings

    for model_id in self.model_ids:
        yield ThinkingIndicator(model=model_id)
        prompt = DISCUSSION_PROMPT_LADDER_CLIMB.format(
            language_instruction=get_language_instruction(),
            discussion_history=surviving_ideas,
        )
        response = await self._call_model(model_id, task, prompt)
        yield TeamTextMessage(
            source=model_id,
            content=response,
            method="ladder",
        )

    # Synthesis
    yield await self._run_synthesis_ladder(task, proposals, rankings)
```

### 3.2 Add to Method Dispatcher

In the `run_stream` method, add the case:

```python
async def run_stream(self, task: str):
    """Stream discussion messages."""
    method = self.method_override or "standard"

    if method == "standard":
        async for msg in self._run_standard_flow(task):
            yield msg
    elif method == "oxford":
        async for msg in self._run_oxford_flow(task):
            yield msg
    # ... other methods ...
    elif method == "ladder":  # ADD THIS
        async for msg in self._run_ladder_flow(task):
            yield msg
    else:
        raise ValueError(f"Unknown method: {method}")
```

## Step 4: Update IPC (`ipc.py`)

Add `"ladder"` to the validation set:

```python
VALID_METHODS = {
    "standard", "oxford", "advocate", "socratic",
    "delphi", "brainstorm", "tradeoff",
    "ladder"  # ADD THIS
}
```

## Step 5: Update Frontend

### 5.1 TypeScript Types (`protocol.ts`)

```typescript
// Add to the DiscussionMethod type
export type DiscussionMethod =
  | "standard"
  | "oxford"
  | "advocate"
  | "socratic"
  | "delphi"
  | "brainstorm"
  | "tradeoff"
  | "ladder";  // ADD THIS
```

### 5.2 Store (`store/index.ts`)

Add the method to any method lists or switch statements.

### 5.3 UI Components

Update method selector and any method-specific UI:

```typescript
const METHOD_INFO = {
  // ... existing methods ...
  ladder: {
    name: "Ladder",
    description: "Iterative elimination: Propose → Rank → Climb",
    minModels: 3,
    icon: "🪜",
  },
};
```

## Step 6: Write Tests

### 6.1 Flow Test (`test_method_flows.py`)

```python
@pytest.mark.asyncio
async def test_ladder_flow():
    """Test Ladder method produces expected phases."""
    from quorum.team import FourPhaseConsensusTeam

    # Mock models
    model_ids = ["model-a", "model-b", "model-c"]
    team = FourPhaseConsensusTeam(
        model_ids=model_ids,
        method_override="ladder",
    )

    recording = await run_and_record(team, "What's the best approach?")

    # Verify phase sequence
    phases = recording.phase_markers()
    assert len(phases) == 3
    assert phases[0].message == "Phase 1: Propose Solutions"
    assert phases[1].message == "Phase 2: Rank and Eliminate"
    assert phases[2].message == "Phase 3: Climb to Consensus"

    # Verify all models participated in Phase 1
    phase1_answers = recording.messages_in_phase(1)
    assert len(phase1_answers) == 3
    assert all(isinstance(m, IndependentAnswer) for m in phase1_answers)
```

### 6.2 Validation Test (`test_agents.py`)

```python
def test_ladder_requires_three_models():
    """Test Ladder method requires at least 3 models."""
    from quorum.agents import validate_method_model_count

    valid, error = validate_method_model_count("ladder", 2)
    assert not valid
    assert "at least 3" in error.lower()

    valid, error = validate_method_model_count("ladder", 3)
    assert valid
    assert error is None
```

## Step 7: Update Documentation

### 7.1 README.md

Add a section under "Discussion Methods":

```markdown
### Ladder

**Requires:** 3+ models

Iterative elimination process. Models propose multiple solutions,
rank them collectively, eliminate weaker ideas, then refine the
survivors into a final answer.

**Flow:**
```
Phase 1         Phase 2         Phase 3
┌───────────┐   ┌───────────┐   ┌───────────┐
│  Propose  │ → │   Rank    │ → │   Climb   │
│(parallel) │   │  (vote)   │   │  (refine) │
└───────────┘   └───────────┘   └───────────┘
3 ideas each    Top 3 survive   Build best answer
```

**Best for:** Brainstorming with elimination, finding optimal solutions.
```

### 7.2 IPC Protocol Doc

Add the method to the valid methods list in `docs/api/IPC_PROTOCOL.md`.

## Step 8: Test End-to-End

```bash
# Run unit tests
pytest tests/test_agents.py tests/test_method_flows.py -v -k ladder

# Build frontend
cd frontend && npm run build && cd ..

# Test manually
./quorum
> /method ladder
> What's the best way to organize this codebase?
```

## Checklist

- [ ] Prompts added to `agents.py`
- [ ] Validation added to `agents.py`
- [ ] Flow method added to `team.py`
- [ ] Dispatcher case added to `team.py`
- [ ] Method added to `VALID_METHODS` in `ipc.py`
- [ ] TypeScript types updated
- [ ] Store/UI updated
- [ ] Flow tests written
- [ ] Validation tests written
- [ ] README updated
- [ ] IPC Protocol doc updated
- [ ] Protocol version bumped (minor)
- [ ] CHANGELOG updated
- [ ] End-to-end test passed

## Tips

- **Start simple**: Get the basic flow working before adding special features
- **Test incrementally**: Run tests after each major change
- **Match existing patterns**: Look at how Oxford or Delphi are implemented
- **Consider edge cases**: What if a model times out? What if rankings conflict?
- **Document decisions**: Add comments explaining non-obvious choices
