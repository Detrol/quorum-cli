# ADR-0004: Seven Discussion Methods for Multi-Agent Deliberation

## Status

Accepted

## Context

Quorum orchestrates AI model discussions, but a single discussion format doesn't fit all question types:
- Technical questions benefit from collaborative exploration
- Binary decisions need structured debate
- Estimates require iterative refinement
- Creative problems need ideation phases

Users need different "lenses" to examine problems effectively.

## Decision

Implement **seven distinct discussion methods**, each with specific phases and role assignments:

### 1. Standard (Default)
**Phases**: Answer → Critique → Discuss → Position → Synthesis

Balanced consensus-seeking. All models participate equally in round-robin discussion.

**Best for**: General technical questions, best practices, problem-solving.

### 2. Oxford
**Phases**: Opening → Rebuttal → Closing → Synthesis

Formal debate with FOR/AGAINST teams. Models are assigned positions regardless of personal opinion.

**Best for**: Binary decisions, exploring both sides of controversial topics.

**Constraint**: Requires even number of models.

### 3. Advocate
**Phases**: Positions → Cross-Examination → Synthesis

Devil's advocate mode. One model (last selected) challenges the emerging consensus while others defend.

**Best for**: Stress-testing ideas, avoiding groupthink, critical analysis.

**Constraint**: Requires 3+ models.

### 4. Socratic
**Phases**: Thesis → Elenchus (Q&A) → Synthesis

Question-driven dialogue. Models take turns as questioner, probing assumptions and reasoning.

**Best for**: Deep exploration, exposing hidden assumptions, philosophical questions.

### 5. Delphi
**Phases**: Round 1 → Round 2 → Round 3 → Aggregate

Iterative estimation. Models provide independent estimates, then revise after seeing (anonymous) group estimates.

**Best for**: Time estimates, cost projections, quantitative forecasting.

**Constraint**: Requires 3+ models.

### 6. Brainstorm
**Phases**: Diverge → Build → Converge → Synthesis

Creative ideation. Generate ideas without judgment, then combine and evaluate.

**Best for**: Feature ideation, creative problem-solving, exploring possibilities.

### 7. Tradeoff
**Phases**: Frame → Criteria → Evaluate → Recommend

Structured comparison. Define alternatives, establish criteria, score systematically.

**Best for**: Technology choices, A vs B decisions, vendor selection.

## Consequences

### Positive

- **Right tool for the job**: Users can match method to question type
- **Structured thinking**: Methods enforce useful cognitive patterns
- **Role diversity**: FOR/AGAINST, questioner/respondent create productive tension
- **Iterative refinement**: Delphi allows estimates to converge
- **Creativity support**: Brainstorm separates divergent/convergent thinking

### Negative

- **Complexity**: 7 methods = 7 different code paths to maintain
- **Learning curve**: Users must understand when to use each method
- **Model constraints**: Some methods require specific model counts
- **Testing burden**: Each method needs integration tests

### Neutral

- Methods share common patterns (parallel phases, synthesis)
- Inline syntax (`/oxford Question`) makes switching easy
- Default (Standard) works well for most cases

## Implementation

Each method is implemented as a flow in `FourPhaseConsensusTeam`:
- `_run_standard_flow()`
- `_run_oxford_flow()`
- `_run_advocate_flow()`
- `_run_socratic_flow()`
- `_run_delphi_flow()`
- `_run_brainstorm_flow()`
- `_run_tradeoff_flow()`

Shared patterns:
- Parallel execution: `asyncio.gather()` for independent phases
- Role assignment: Via message `role` field (FOR, AGAINST, QUESTIONER, etc.)
- Phase markers: `PhaseMarker` events signal UI transitions
- Synthesis: Final model aggregates all positions

## Alternatives Considered

### Single Flexible Method

One configurable method with parameters. Rejected because:
- Too many parameters to configure
- Loses clear mental models
- Hard to document and teach

### Unlimited Custom Methods

Let users define their own flows. Rejected because:
- Complexity explosion
- No quality control
- Hard to support/debug

### Three Methods (Simple/Debate/Creative)

Minimal set. Rejected because:
- Loses nuance (Socratic vs Standard, Delphi vs Standard)
- "Debate" conflates Oxford, Advocate
- Users asked for estimation-specific method

## References

- [Oxford Union Debate Format](https://en.wikipedia.org/wiki/Oxford-style_debate)
- [Delphi Method](https://en.wikipedia.org/wiki/Delphi_method)
- [Socratic Method](https://en.wikipedia.org/wiki/Socratic_method)
- `src/quorum/agents.py` - Method prompts and validation
- `src/quorum/team.py` - Flow implementations
