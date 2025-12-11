# Quorum Integration Examples

This directory contains examples showing how to integrate with Quorum's IPC protocol.

## Examples

### Python Client (`python_ipc_client.py`)

A minimal Python client that connects to the Quorum backend via JSON-RPC.

```bash
# Run from project root
python examples/python_ipc_client.py
```

**Features demonstrated:**
- Spawning the backend process
- Sending JSON-RPC requests
- Handling events during discussion
- Clean shutdown

### Node.js Client (`node_ipc_client.js`)

A minimal Node.js client showing the same integration pattern.

```bash
# Run from project root
node examples/node_ipc_client.js
```

**Features demonstrated:**
- Process management with child_process
- Line-based JSON parsing
- Event handling
- Async/await patterns

## Protocol Reference

See [docs/api/IPC_PROTOCOL.md](../docs/api/IPC_PROTOCOL.md) for the complete protocol specification.

## Quick Start

1. Ensure Quorum is installed: `./install.sh`
2. Configure API keys in `.env`
3. Run an example: `python examples/python_ipc_client.py`

## Building Your Own Integration

The key patterns for any integration:

1. **Spawn the backend** with `--ipc` flag
2. **Wait for `ready` event** before sending requests
3. **Send JSON-RPC requests** as newline-delimited JSON to stdin
4. **Read responses and events** line-by-line from stdout
5. **Handle events** during long-running operations like `run_discussion`
6. **Close stdin** to signal shutdown
