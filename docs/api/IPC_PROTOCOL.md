# Quorum IPC Protocol Specification

**Protocol Version:** 1.0.0

This document specifies the JSON-RPC 2.0 based IPC protocol used for communication between the Quorum frontend and backend.

## Transport

- **Transport:** stdin/stdout
- **Format:** NDJSON (Newline-Delimited JSON)
- **Encoding:** UTF-8

Each message is a single JSON object followed by a newline character (`\n`). Messages must not contain embedded newlines within the JSON.

## Protocol Version

The protocol uses semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR:** Incremented for breaking changes
- **MINOR:** Incremented for backward-compatible additions
- **PATCH:** Incremented for backward-compatible fixes

Frontend and backend should check protocol versions during initialization and warn if they differ.

## Message Types

### Request (Frontend → Backend)

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "method_name",
  "params": {}
}
```

### Response (Backend → Frontend)

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {}
}
```

### Error Response

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32000,
    "message": "Error description",
    "data": null
  }
}
```

### Notification/Event (Backend → Frontend)

```json
{
  "jsonrpc": "2.0",
  "method": "event_name",
  "params": {}
}
```

Events have no `id` field and do not expect a response.

---

## Lifecycle

### Startup Sequence

1. Frontend spawns backend process with `--ipc` flag
2. Backend emits `ready` event
3. Frontend sends `initialize` request
4. Backend responds with capabilities and protocol version
5. Frontend sends `list_models` request
6. Normal operation begins

### Shutdown

Frontend closes stdin → Backend reads EOF → Backend exits cleanly.

---

## Methods

### initialize

Initialize the backend and check protocol compatibility.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocol_version": "1.0.0"
  }
}
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `protocol_version` | string | No | Frontend's protocol version for compatibility check |

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "name": "quorum-cli",
    "version": "1.0.0",
    "protocol_version": "1.0.0",
    "providers": ["openai", "anthropic", "google", "xai"],
    "version_warning": null
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Backend name |
| `version` | string | Backend version |
| `protocol_version` | string | Backend protocol version |
| `providers` | string[] | Available AI providers |
| `version_warning` | string \| null | Warning if version mismatch detected |

---

### list_models

Get all available models grouped by provider.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "list_models",
  "params": {}
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "models": {
      "openai": [
        {"id": "gpt-4o", "provider": "openai", "display_name": "GPT-4o"}
      ],
      "anthropic": [
        {"id": "claude-sonnet-4-5", "provider": "anthropic", "display_name": "Claude Sonnet"}
      ]
    },
    "validated": ["gpt-4o", "claude-sonnet-4-5"]
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `models` | object | Models grouped by provider |
| `models[provider]` | ModelInfo[] | Array of model info objects |
| `validated` | string[] | Cached validated model IDs |

**ModelInfo:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Model identifier (e.g., "gpt-4o") |
| `provider` | string | Provider name |
| `display_name` | string \| null | Human-readable name |

---

### validate_model

Validate a model by making a test API call.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "validate_model",
  "params": {
    "model_id": "gpt-4o"
  }
}
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model_id` | string | Yes | Model ID to validate |

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "valid": true,
    "error": null
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `valid` | boolean | Whether the model is valid |
| `error` | string \| null | Error message if validation failed |

---

### get_config

Get current backend configuration.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "get_config",
  "params": {}
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "result": {
    "rounds_per_agent": 2,
    "synthesizer_mode": "first",
    "default_language": null,
    "available_providers": ["openai", "anthropic"],
    "log_dir": "/home/user/.quorum/logs",
    "export_dir": "/home/user/.quorum/exports",
    "export_format": "md"
  }
}
```

---

### get_user_settings

Get cached user settings.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "method": "get_user_settings",
  "params": {}
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "result": {
    "selected_models": ["gpt-4o", "claude-sonnet-4-5"],
    "discussion_method": "standard",
    "synthesizer_mode": "first",
    "max_turns": null
  }
}
```

---

### save_user_settings

Save user settings (merges with existing).

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 6,
  "method": "save_user_settings",
  "params": {
    "selected_models": ["gpt-4o", "claude-sonnet-4-5"],
    "discussion_method": "oxford"
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 6,
  "result": {
    "status": "saved"
  }
}
```

---

### get_input_history

Get cached input history.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "method": "get_input_history",
  "params": {}
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "result": {
    "history": ["What is AI?", "How does consensus work?"]
  }
}
```

---

### add_to_input_history

Add an input to history.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 8,
  "method": "add_to_input_history",
  "params": {
    "input": "New question here"
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 8,
  "result": {
    "status": "added"
  }
}
```

---

### run_discussion

Start a multi-agent discussion. This is a long-running operation that emits events during execution.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 9,
  "method": "run_discussion",
  "params": {
    "question": "What is the best programming language?",
    "model_ids": ["gpt-4o", "claude-sonnet-4-5"],
    "options": {
      "method": "standard",
      "max_turns": 6,
      "synthesizer_mode": "first",
      "role_assignments": null
    }
  }
}
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `question` | string | Yes | The discussion topic/question (max 50KB) |
| `model_ids` | string[] | Yes | 2-20 model IDs to participate |
| `options.method` | string | No | Discussion method (default: "standard") |
| `options.max_turns` | number | No | Maximum discussion turns (1-100) |
| `options.synthesizer_mode` | string | No | "first", "random", or "rotate" |
| `options.role_assignments` | object | No | Custom role assignments for team methods |

**Valid Methods:**
- `standard` - Consensus-seeking (2+ models)
- `oxford` - Formal debate (even number of models)
- `advocate` - Devil's advocate (3+ models)
- `socratic` - Socratic dialogue (2+ models)
- `delphi` - Iterative estimation (3+ models)
- `brainstorm` - Creative ideation (2+ models)
- `tradeoff` - Structured comparison (2+ models)

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 9,
  "result": {
    "status": "completed"
  }
}
```

Note: Response is sent only after the discussion completes. Events are emitted during execution.

---

### cancel_discussion

Cancel a running discussion.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 10,
  "method": "cancel_discussion",
  "params": {}
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 10,
  "result": {
    "status": "cancellation_requested"
  }
}
```

---

### resume_discussion

Resume a paused discussion (after phase transition).

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 11,
  "method": "resume_discussion",
  "params": {}
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 11,
  "result": {
    "status": "resumed"
  }
}
```

---

### get_role_assignments

Get role assignments for a team debate method.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 12,
  "method": "get_role_assignments",
  "params": {
    "method": "oxford",
    "model_ids": ["gpt-4o", "claude-sonnet-4-5", "gemini-pro", "grok-2"]
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 12,
  "result": {
    "assignments": {
      "FOR": ["gpt-4o", "gemini-pro"],
      "AGAINST": ["claude-sonnet-4-5", "grok-2"]
    }
  }
}
```

---

### swap_role_assignments

Swap team assignments (FOR↔AGAINST).

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 13,
  "method": "swap_role_assignments",
  "params": {
    "assignments": {
      "FOR": ["gpt-4o"],
      "AGAINST": ["claude-sonnet-4-5"]
    }
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 13,
  "result": {
    "assignments": {
      "FOR": ["claude-sonnet-4-5"],
      "AGAINST": ["gpt-4o"]
    }
  }
}
```

---

### analyze_question

Analyze a question and recommend the best discussion method.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 14,
  "method": "analyze_question",
  "params": {
    "question": "How long will this migration take?"
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 14,
  "result": {
    "advisor_model": "gpt-4o-mini",
    "recommendations": {
      "primary": {
        "method": "delphi",
        "confidence": 95,
        "reason": "Estimation questions work best with Delphi method"
      },
      "alternatives": [
        {
          "method": "standard",
          "confidence": 60,
          "reason": "Could work for general discussion"
        }
      ]
    }
  }
}
```

---

## Events

Events are emitted by the backend during discussion execution.

### ready

Emitted when backend is ready to accept requests.

```json
{
  "jsonrpc": "2.0",
  "method": "ready",
  "params": {
    "version": "1.0.0",
    "protocol_version": "1.0.0"
  }
}
```

---

### phase_start

Emitted when a new phase begins.

```json
{
  "jsonrpc": "2.0",
  "method": "phase_start",
  "params": {
    "phase": 1,
    "message": "Phase 1: Independent Answers",
    "num_participants": 3,
    "method": "standard",
    "total_phases": 5
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `phase` | number | Phase number (1-based) |
| `message` | string | Human-readable phase description |
| `num_participants` | number | Number of participating models |
| `method` | string | Discussion method being used |
| `total_phases` | number | Total phases in this method |

---

### phase_complete

Emitted when a phase completes (triggers pause before next phase).

```json
{
  "jsonrpc": "2.0",
  "method": "phase_complete",
  "params": {
    "completed_phase": 1,
    "next_phase": 2,
    "next_phase_message": "Phase 2: Cross-Examination",
    "method": "advocate"
  }
}
```

---

### pause_timeout

Emitted when pause times out and auto-resumes (5 minutes).

```json
{
  "jsonrpc": "2.0",
  "method": "pause_timeout",
  "params": {
    "message": "Auto-resuming after timeout",
    "timeout_seconds": 300
  }
}
```

---

### thinking

Emitted when a model is generating a response.

```json
{
  "jsonrpc": "2.0",
  "method": "thinking",
  "params": {
    "model": "gpt-4o"
  }
}
```

---

### independent_answer

Emitted for Phase 1 independent answers.

```json
{
  "jsonrpc": "2.0",
  "method": "independent_answer",
  "params": {
    "source": "gpt-4o",
    "content": "I believe Python is the best..."
  }
}
```

---

### critique

Emitted for Phase 2 critiques.

```json
{
  "jsonrpc": "2.0",
  "method": "critique",
  "params": {
    "source": "claude-sonnet-4-5",
    "agreements": "I agree that Python is accessible...",
    "disagreements": "However, I disagree about...",
    "missing": "The discussion hasn't considered..."
  }
}
```

---

### chat_message

Emitted during discussion phases and team debates.

```json
{
  "jsonrpc": "2.0",
  "method": "chat_message",
  "params": {
    "source": "gpt-4o",
    "content": "Building on the previous points...",
    "role": "FOR",
    "round_type": "opening",
    "method": "oxford"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `source` | string | Model that generated this message |
| `content` | string | Message content |
| `role` | string \| null | Team role (FOR, AGAINST, ADVOCATE, etc.) |
| `round_type` | string \| null | Round type (opening, rebuttal, closing) |
| `method` | string | Discussion method |

---

### final_position

Emitted for Phase 4 final positions.

```json
{
  "jsonrpc": "2.0",
  "method": "final_position",
  "params": {
    "source": "gemini-pro",
    "position": "Python is the best choice for beginners.",
    "confidence": "HIGH"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `source` | string | Model |
| `position` | string | Final position statement |
| `confidence` | string | "HIGH", "MEDIUM", or "LOW" |

---

### synthesis

Emitted for the final synthesis.

```json
{
  "jsonrpc": "2.0",
  "method": "synthesis",
  "params": {
    "consensus": "YES",
    "synthesis": "All models agree that Python is best for beginners...",
    "differences": "Minor disagreements about JavaScript as an alternative...",
    "synthesizer_model": "gpt-4o",
    "confidence_breakdown": {
      "gpt-4o": 90,
      "claude-sonnet-4-5": 85,
      "gemini-pro": 88
    },
    "message_count": 12,
    "method": "standard"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `consensus` | string | "YES", "PARTIAL", "NO", "FOR", "AGAINST", etc. |
| `synthesis` | string | Synthesized final answer |
| `differences` | string | Key remaining differences |
| `synthesizer_model` | string | Model that created synthesis |
| `confidence_breakdown` | object | Confidence scores per model |
| `message_count` | number | Total messages in discussion |
| `method` | string | Discussion method used |

---

### discussion_complete

Emitted when discussion finishes successfully.

```json
{
  "jsonrpc": "2.0",
  "method": "discussion_complete",
  "params": {
    "messages_count": 15
  }
}
```

---

### discussion_error

Emitted when an error occurs during discussion.

```json
{
  "jsonrpc": "2.0",
  "method": "discussion_error",
  "params": {
    "error": "API rate limit exceeded"
  }
}
```

---

### discussion_cancelled

Emitted when discussion is cancelled by user.

```json
{
  "jsonrpc": "2.0",
  "method": "discussion_cancelled",
  "params": {}
}
```

---

## Error Codes

| Code | Meaning |
|------|---------|
| -32700 | Parse error (invalid JSON) |
| -32600 | Invalid Request (missing required fields) |
| -32601 | Method not found |
| -32602 | Invalid params |
| -32603 | Internal error |
| -32000 | Application error (custom) |

---

## Input Validation

The backend validates all input parameters:

| Parameter | Constraint |
|-----------|------------|
| `question` | Max 50,000 characters |
| `model_ids` | 2-20 models, each max 100 chars |
| `model_id` | Must match pattern `^[a-zA-Z0-9][a-zA-Z0-9\-\./:_]*$` |
| `method` | Must be one of valid methods |
| `max_turns` | 1-100 |

---

## Flow Control

### Discussion Pause/Resume

1. When a phase completes (except phase 1), backend emits `phase_complete`
2. Backend waits for `resume_discussion` request
3. If no resume within 5 minutes, backend auto-resumes with `pause_timeout` event
4. Frontend should display phase completion and wait for user input

### Concurrent Discussions

Only one discussion can run at a time. Attempting to start a second discussion returns an error.

---

## TypeScript Types

See `frontend/src/ipc/protocol.ts` for TypeScript type definitions.

## Python Implementation

See `src/quorum/ipc.py` for the backend implementation.
