# ADR-0003: Remove AutoGen, Use Direct SDK Clients

## Status

Accepted

## Context

In ADR-0002, we chose AutoGen for multi-agent orchestration. After 6 months of development, we found that:

1. **We only used ~5% of AutoGen**: Just the client abstraction (`OpenAIChatCompletionClient`, `AnthropicChatCompletionClient`) and message types (`SystemMessage`, `UserMessage`)

2. **All orchestration was custom**: Our `FourPhaseConsensusTeam` and seven method implementations don't use AutoGen's GroupChat patterns at all

3. **Marketing confusion**: Describing Quorum as "built on AutoGen" was misleading since we don't use AutoGen's agent patterns

4. **Dependency overhead**: AutoGen adds ~50MB of dependencies for features we don't use

## Decision

Remove AutoGen entirely and use direct SDK clients (`openai`, `anthropic` packages) with a thin custom wrapper.

### New Architecture

```
src/quorum/clients/
├── __init__.py           # Re-exports
├── types.py              # Message dataclasses + ChatClient protocol
├── openai_client.py      # OpenAI-compatible (OpenAI, Google, xAI, Ollama)
└── anthropic_client.py   # Anthropic client
```

### Key Components

**Message Types** (`types.py`):
```python
@dataclass
class SystemMessage:
    content: str
    source: str = "system"

@dataclass
class UserMessage:
    content: str
    source: str = "user"
```

**ChatClient Protocol** (`types.py`):
```python
@runtime_checkable
class ChatClient(Protocol):
    model: str
    async def create(self, messages: list[Message]) -> str: ...
```

**OpenAIClient** (`openai_client.py`):
- Uses `openai.AsyncOpenAI` directly
- Supports OpenAI, Google, xAI, and Ollama via `base_url` parameter
- Connection pooling via shared `httpx.AsyncClient`

**AnthropicClient** (`anthropic_client.py`):
- Uses `anthropic.AsyncAnthropic` directly
- Handles Anthropic's separate system message parameter

## Consequences

### Positive

- **~50MB smaller**: Removed `autogen-agentchat` and `autogen-ext` packages
- **Faster startup**: Less imports to load
- **Clearer architecture**: No confusion about what framework we use
- **Full control**: No dependency on AutoGen's release cycle
- **Simpler debugging**: Direct SDK calls are easier to trace

### Negative

- **Maintenance**: We now maintain ~200 lines of client code
- **Feature parity**: Must implement any new provider support ourselves

### Migration

No breaking changes to the public API. Internal changes:

| Before | After |
|--------|-------|
| `from autogen_core.models import SystemMessage` | `from .clients import SystemMessage` |
| `OpenAIChatCompletionClient(...)` | `OpenAIClient(...)` |
| `AnthropicChatCompletionClient(...)` | `AnthropicClient(...)` |

## References

- ADR-0002: Original AutoGen decision (now superseded)
- `src/quorum/clients/` - New client implementation
- `src/quorum/models.py` - Updated client factory
