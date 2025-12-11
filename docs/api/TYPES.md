# Quorum Type Boundary Documentation

This document defines the canonical types used at the Python/TypeScript boundary. When modifying these types, **update both implementations** to maintain compatibility.

## Source Files

| Language | File | Purpose |
|----------|------|---------|
| TypeScript | `frontend/src/ipc/protocol.ts` | Canonical type definitions |
| Python | `src/quorum/ipc.py` | Event emission (inline dicts) |
| Python | `src/quorum/team.py` | Message dataclasses |

## Protocol Constants

Both implementations must agree on these values:

| Constant | Value | TypeScript | Python |
|----------|-------|------------|--------|
| Protocol Version | `"1.0.0"` | `protocol.ts:14` | `constants.py:13` |
| Max Question Length | `50000` | - | `constants.py:33` |
| Max Models | `20` | - | `constants.py:27` |
| Max Model ID Length | `100` | - | `constants.py:30` |

---

## Enumerations

### DiscussionMethod

Valid discussion method identifiers.

```typescript
// TypeScript
type DiscussionMethod = "standard" | "oxford" | "advocate" | "socratic" | "delphi" | "brainstorm" | "tradeoff";
```

```python
# Python
VALID_METHODS = {"standard", "oxford", "advocate", "socratic", "delphi", "brainstorm", "tradeoff"}
```

### SynthesizerMode

How the synthesizer model is selected.

```typescript
// TypeScript
type SynthesizerMode = "first" | "random" | "rotate";
```

```python
# Python
VALID_SYNTHESIZER_MODES = {"first", "random", "rotate"}
```

### Confidence

Confidence levels for final positions.

```typescript
// TypeScript
type Confidence = "HIGH" | "MEDIUM" | "LOW";
```

```python
# Python - parsed from model response text
# Normalized to uppercase before emission
```

### Consensus

Synthesis consensus outcomes.

```typescript
// TypeScript
type Consensus = "YES" | "PARTIAL" | "NO" | "FOR" | "AGAINST" | string;
// Note: Also includes method-specific outcomes like "X SELECTED" for brainstorm
```

### TeamRole

Roles assigned in team-based discussion methods.

```typescript
// TypeScript
type TeamRole = "FOR" | "AGAINST" | "ADVOCATE" | "DEFENDER" | "QUESTIONER" | "RESPONDENT" | "PANELIST" | "IDEATOR" | "EVALUATOR" | null;
```

| Role | Methods | Description |
|------|---------|-------------|
| `FOR` | Oxford | Argues in favor of the motion |
| `AGAINST` | Oxford | Argues against the motion |
| `ADVOCATE` | Advocate | Devil's advocate challenger |
| `DEFENDER` | Advocate | Defends the consensus |
| `QUESTIONER` | Socratic | Asks probing questions |
| `RESPONDENT` | Socratic | Answers questions |
| `PANELIST` | Delphi | Anonymous estimator |
| `IDEATOR` | Brainstorm | Generates ideas |
| `EVALUATOR` | Brainstorm, Tradeoff | Evaluates options |
| `null` | Standard | No assigned role |

### RoundType

Round types within team debates.

```typescript
// TypeScript
type RoundType = "opening" | "rebuttal" | "closing" | null;
```

| Round | Methods | Description |
|-------|---------|-------------|
| `opening` | Oxford | Initial arguments |
| `rebuttal` | Oxford | Counter-arguments |
| `closing` | Oxford | Final statements |
| `null` | Others | Not applicable |

---

## Data Types

### ModelInfo

Information about an available AI model.

```typescript
// TypeScript
interface ModelInfo {
  id: string;           // e.g., "gpt-4o", "claude-sonnet-4-5"
  provider: string;     // e.g., "openai", "anthropic"
  display_name: string | null;  // Human-readable name
}
```

```python
# Python (emitted as dict)
{
    "id": "gpt-4o",
    "provider": "openai",
    "display_name": "GPT-4o"
}
```

### IndependentAnswerEvent

Phase 1: Model's independent answer to the question.

```typescript
// TypeScript
interface IndependentAnswerEvent {
  source: string;   // Model ID
  content: string;  // Full response text
}
```

```python
# Python emission (ipc.py)
self._emit_event("independent_answer", {
    "source": answer.source,
    "content": answer.content,
})
```

### CritiqueEvent

Phase 2: Structured critique of other models' answers.

```typescript
// TypeScript
interface CritiqueEvent {
  source: string;        // Model ID
  agreements: string;    // Points of agreement
  disagreements: string; // Points of disagreement
  missing: string;       // Missing considerations
}
```

```python
# Python dataclass (team.py)
@dataclass
class CritiqueResponse:
    source: str
    agreements: str
    disagreements: str
    missing: str
```

### ChatMessageEvent

Discussion phase message with optional role context.

```typescript
// TypeScript
interface ChatMessageEvent {
  source: string;
  content: string;
  role?: TeamRole;
  round_type?: RoundType;
  method?: DiscussionMethod;
}
```

```python
# Python dataclass (team.py)
@dataclass
class TeamTextMessage:
    content: str
    source: str
    role: str | None = None
    round_type: str | None = None
```

### FinalPositionEvent

Phase 4: Model's final stance with confidence.

```typescript
// TypeScript
interface FinalPositionEvent {
  source: string;
  position: string;
  confidence: "HIGH" | "MEDIUM" | "LOW";
}
```

```python
# Python dataclass (team.py)
@dataclass
class FinalPosition:
    source: str
    position: str
    confidence: str  # "HIGH", "MEDIUM", or "LOW"
```

### SynthesisEvent

Final synthesis aggregating all positions.

```typescript
// TypeScript
interface SynthesisEvent {
  consensus: string;  // YES/PARTIAL/NO or method-specific
  synthesis: string;  // Synthesized answer
  differences: string;  // Remaining disagreements
  synthesizer_model: string;  // Which model synthesized
  confidence_breakdown: Record<string, number>;  // Model -> confidence %
  message_count: number;  // Total messages
  method?: DiscussionMethod;
}
```

```python
# Python dataclass (team.py)
@dataclass
class SynthesisResult:
    consensus: str
    synthesis: str
    differences: str
    synthesizer_model: str
    confidence_breakdown: dict[str, int]
    message_count: int
```

### PhaseStartEvent

Signals the beginning of a discussion phase.

```typescript
// TypeScript
interface PhaseStartEvent {
  phase: number;           // 1-based phase number
  message: string;         // Human-readable description
  num_participants: number;
  method?: DiscussionMethod;
  total_phases?: number;
}
```

### PhaseCompleteEvent

Signals phase completion and pause before next phase.

```typescript
// TypeScript
interface PhaseCompleteEvent {
  completed_phase: number;
  next_phase: number;
  next_phase_message?: string;
  method?: string;
}
```

---

## Type Mapping Reference

| Concept | TypeScript | Python |
|---------|------------|--------|
| Optional string | `string \| null` | `str \| None` |
| Optional number | `number \| null` | `int \| None` |
| String dictionary | `Record<string, T>` | `dict[str, T]` |
| Array | `T[]` | `list[T]` |
| Union types | `"a" \| "b"` | `Literal["a", "b"]` |
| Interface | `interface Foo { ... }` | `@dataclass class Foo` |

---

## Validation Rules

These rules are enforced by the Python backend:

| Field | Rule | Error Code |
|-------|------|------------|
| `model_id` | Matches `^[a-zA-Z0-9][a-zA-Z0-9\-\./:_]*$` | -32602 |
| `model_id` | Max 100 characters | -32602 |
| `model_ids` | 2-20 models | -32602 |
| `question` | Max 50,000 characters | -32602 |
| `max_turns` | 1-100 | -32602 |
| `method` | Must be valid method | -32602 |

---

## Adding New Types

When adding a new event or type:

1. **Define TypeScript interface** in `frontend/src/ipc/protocol.ts`
2. **Add to EventMap** if it's an event
3. **Create Python dataclass** in `src/quorum/team.py` (if needed)
4. **Emit event** in `src/quorum/ipc.py` with matching structure
5. **Handle in frontend** in `App.tsx` event handler
6. **Update this document**

## Version Compatibility

The protocol uses semantic versioning:

| Change Type | Version Bump | Example |
|-------------|--------------|---------|
| Breaking (field removed) | MAJOR | 1.x → 2.0 |
| Addition (new event/field) | MINOR | 1.1 → 1.2 |
| Bug fix | PATCH | 1.1.0 → 1.1.1 |

Frontend and backend check versions during initialization. Mismatched MAJOR versions will warn users.
