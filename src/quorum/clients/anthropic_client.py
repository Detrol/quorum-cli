"""Anthropic client for Claude models.

Anthropic's API has a different structure than OpenAI:
- System messages are passed as a separate parameter, not in the messages list
- Response format differs (content is a list of content blocks)
"""

from __future__ import annotations

from anthropic import AsyncAnthropic

from .types import AssistantMessage, Message, SystemMessage, UserMessage


class AnthropicClient:
    """Client for Anthropic's Claude API."""

    def __init__(self, model: str, api_key: str, effort: str | None = None):
        """Initialize the Anthropic client.

        Args:
            model: Model identifier (e.g., "claude-sonnet-4-20250514").
            api_key: Anthropic API key.
            effort: Optional effort (low/medium/high/xhigh/max) with adaptive thinking.
                Models without effort support (e.g. Haiku 4.5) reject it.
        """
        self.model = model
        self.effort = effort
        self._api_key: str | None = api_key
        self._client = AsyncAnthropic(api_key=api_key)

    async def create(self, messages: list[Message]) -> str:
        """Send messages to Claude and get a response.

        Args:
            messages: List of messages forming the conversation.

        Returns:
            The model's response text.

        Raises:
            anthropic.APIError: If the API request fails.
        """
        # Anthropic handles system messages separately
        system_content: str | None = None
        conversation_messages: list[dict[str, str]] = []

        for msg in messages:
            if isinstance(msg, SystemMessage):
                # Anthropic only supports one system message
                system_content = msg.content
            elif isinstance(msg, UserMessage):
                conversation_messages.append({
                    "role": "user",
                    "content": msg.content,
                })
            elif isinstance(msg, AssistantMessage):
                conversation_messages.append({
                    "role": "assistant",
                    "content": msg.content,
                })

        # Build request kwargs
        kwargs: dict = {
            "model": self.model,
            "messages": conversation_messages,
            "max_tokens": 4096,
        }

        # Only include system if provided
        if system_content:
            kwargs["system"] = system_content

        if self.effort:
            # Thinking shares max_tokens with the answer, so give it room
            kwargs["max_tokens"] = 16000
            kwargs["thinking"] = {"type": "adaptive"}
            kwargs["output_config"] = {"effort": self.effort}

        response = await self._client.messages.create(**kwargs)

        # Extract text from response content blocks
        # Anthropic returns content as a list of content blocks
        text_parts = []
        for block in response.content:
            if hasattr(block, "text"):
                text_parts.append(block.text)

        return "".join(text_parts)
