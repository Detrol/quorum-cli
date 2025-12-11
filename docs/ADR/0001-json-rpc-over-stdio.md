# ADR-0001: JSON-RPC over stdio for Frontend-Backend Communication

## Status

Accepted

## Context

Quorum consists of two processes:
1. **Backend** (Python): Orchestrates AI model discussions using AutoGen
2. **Frontend** (TypeScript/Ink): Terminal UI for user interaction

These processes need to communicate bidirectionally:
- Frontend sends commands (start discussion, select models, pause/resume)
- Backend streams events (model responses, phase transitions, synthesis results)

We needed a protocol that supports:
- Bidirectional async messaging
- Structured data with type safety
- Streaming (backend can send multiple events without waiting for response)
- Cross-platform compatibility (Windows, Linux, macOS)

## Decision

Use **JSON-RPC 2.0 over standard input/output (stdio)** for inter-process communication.

The frontend spawns the backend as a child process with `--ipc` flag and communicates via:
- `stdin`: Frontend → Backend (requests)
- `stdout`: Backend → Frontend (responses + notifications)

Message format follows JSON-RPC 2.0:
```json
// Request (frontend → backend)
{"jsonrpc": "2.0", "method": "start_discussion", "params": {...}, "id": 1}

// Response (backend → frontend)
{"jsonrpc": "2.0", "result": {...}, "id": 1}

// Notification (backend → frontend, no id)
{"jsonrpc": "2.0", "method": "model_response", "params": {...}}
```

Protocol version is negotiated at startup via `initialize` handshake.

## Consequences

### Positive

- **Simple deployment**: No network setup, ports, or security configuration
- **Platform agnostic**: Works identically on Windows, Linux, macOS
- **Well-defined protocol**: JSON-RPC 2.0 is a standard with clear semantics
- **Language agnostic**: Easy to implement in any language
- **Testable**: Can test backend independently by piping JSON
- **No dependencies**: Built into every language's standard library

### Negative

- **Single frontend**: Only one frontend can connect (unlike WebSockets)
- **Process coupling**: Frontend must manage backend process lifecycle
- **Debugging complexity**: Can't easily inspect traffic (unlike HTTP)
- **Buffering quirks**: Must handle line buffering correctly on both ends

### Neutral

- Newline-delimited JSON (NDJSON) is standard practice for streaming
- Protocol versioning allows future evolution

## Alternatives Considered

### WebSockets

Would allow multiple frontends and network-based communication. Rejected because:
- Adds complexity (port allocation, CORS, security)
- Overkill for single-user CLI application
- Platform-specific socket handling

### HTTP REST

Standard web API approach. Rejected because:
- Requires polling for backend events (inefficient)
- No built-in streaming support
- HTTP server overhead unnecessary for local process

### gRPC

High-performance RPC framework. Rejected because:
- Heavy dependency (protobuf, gRPC runtime)
- Overkill for simple request/response patterns
- Compilation step for proto files

### Unix Domain Sockets

Efficient for same-machine IPC. Rejected because:
- Not available on Windows (requires named pipes)
- More complex setup than stdio
- Still requires socket management

## References

- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)
- [Language Server Protocol](https://microsoft.github.io/language-server-protocol/) (uses same pattern)
- `src/quorum/ipc.py` - Backend implementation
- `frontend/src/ipc/` - Frontend implementation
