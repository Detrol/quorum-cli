# ADR-0002: AutoGen for Multi-Agent Orchestration

## Status

Accepted

## Context

Quorum needs to orchestrate structured discussions between multiple AI models. This requires:
- Managing conversation state across multiple turns
- Coordinating parallel and sequential model calls
- Handling different discussion phases with varying logic
- Supporting multiple providers (OpenAI, Anthropic, Google, xAI)
- Error handling and retry logic

Building this from scratch would require significant effort in:
- API client management per provider
- Conversation history management
- Turn-taking logic
- Response streaming

## Decision

Use **Microsoft AutoGen** (v0.4.x) as the multi-agent orchestration framework.

AutoGen provides:
- `AssistantAgent`: Wraps any LLM with conversation management
- `ChatCompletionClient`: Unified interface for OpenAI, Anthropic, etc.
- `GroupChat` patterns: Team-based coordination (though we implement custom flows)
- Async-first design with streaming support

We use AutoGen's low-level primitives:
```python
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.models.anthropic import AnthropicChatCompletionClient
```

But implement our own `FourPhaseConsensusTeam` for custom discussion flows rather than using AutoGen's built-in group chat patterns.

## Consequences

### Positive

- **Provider abstraction**: Single interface for OpenAI, Anthropic, Google APIs
- **Maintained by Microsoft**: Active development, security updates
- **Async/streaming native**: Built for modern Python async patterns
- **Extensible**: Easy to add new providers when released
- **Battle-tested**: Used in production by Microsoft Research

### Negative

- **Dependency weight**: Adds significant dependencies (autogen-agentchat, autogen-ext)
- **Version sensitivity**: 0.4.x API differs significantly from 0.2.x
- **Abstraction mismatch**: AutoGen's group chat patterns don't fit our seven methods
- **Learning curve**: AutoGen concepts (agents, teams, tasks) require understanding

### Neutral

- We use ~20% of AutoGen's features (mainly client abstraction)
- Custom `FourPhaseConsensusTeam` means we're not locked into AutoGen patterns
- Could migrate away if needed by replacing client layer

## Alternatives Considered

### LangChain

Popular LLM framework. Rejected because:
- Heavy abstraction overhead
- Frequent breaking changes
- More focused on RAG/chains than multi-agent
- Larger dependency footprint

### Raw API Clients

Direct `openai`, `anthropic`, `google-genai` packages. Rejected because:
- Would require maintaining 4+ separate client implementations
- No unified streaming interface
- More boilerplate for error handling
- Reinventing wheel for conversation management

### LlamaIndex

Knowledge-focused LLM framework. Rejected because:
- Optimized for RAG, not multi-agent chat
- Less mature agent orchestration
- Heavier than needed for our use case

### CrewAI

Multi-agent framework. Rejected because:
- Less mature than AutoGen
- Smaller community
- More opinionated about agent roles

## References

- [AutoGen Documentation](https://microsoft.github.io/autogen/)
- [AutoGen GitHub](https://github.com/microsoft/autogen)
- `src/quorum/models.py` - Client factory using AutoGen
- `src/quorum/team.py` - Custom team implementation
