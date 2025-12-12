"""Unified client interface for AI providers.

This package provides a consistent interface for communicating with different
AI providers without external orchestration framework dependencies.

Supported providers:
- OpenAI (direct)
- Anthropic (direct)
- Google Gemini (via OpenAI-compatible endpoint)
- xAI Grok (via OpenAI-compatible endpoint)
- Ollama (via OpenAI-compatible endpoint)

Example:
    from quorum.clients import OpenAIClient, SystemMessage, UserMessage

    client = OpenAIClient(model="gpt-4o", api_key="...")
    response = await client.create([
        SystemMessage(content="You are a helpful assistant."),
        UserMessage(content="Hello!"),
    ])
"""

from .anthropic_client import AnthropicClient
from .openai_client import OpenAIClient
from .types import (
    AssistantMessage,
    ChatClient,
    Message,
    SystemMessage,
    UserMessage,
)

__all__ = [
    # Client classes
    "OpenAIClient",
    "AnthropicClient",
    # Message types
    "SystemMessage",
    "UserMessage",
    "AssistantMessage",
    "Message",
    # Protocol
    "ChatClient",
]
