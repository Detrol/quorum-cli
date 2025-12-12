"""Message types and client protocol for AI providers.

This module provides a unified interface for communicating with different
AI providers (OpenAI, Anthropic, Google, xAI, Ollama) without depending
on external orchestration frameworks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class SystemMessage:
    """System message for setting AI behavior and context."""

    content: str
    source: str = "system"


@dataclass
class UserMessage:
    """User message containing the prompt or question."""

    content: str
    source: str = "user"


@dataclass
class AssistantMessage:
    """Assistant message containing a previous AI response."""

    content: str
    source: str = "assistant"


# Type alias for any message type
Message = SystemMessage | UserMessage | AssistantMessage


@runtime_checkable
class ChatClient(Protocol):
    """Protocol defining the interface for chat completion clients.

    All provider-specific clients must implement this protocol to be
    compatible with the connection pool and orchestration layer.
    """

    model: str
    """The model identifier being used by this client."""

    async def create(self, messages: list[Message]) -> str:
        """Send messages to the model and get a response.

        Args:
            messages: List of messages forming the conversation.

        Returns:
            The model's response text.
        """
        ...
