"""OpenAI-compatible client for multiple providers.

This client works with any OpenAI-compatible API:
- OpenAI (direct)
- Google Gemini (via OpenAI-compatible endpoint)
- xAI Grok (via OpenAI-compatible endpoint)
- Ollama (via OpenAI-compatible endpoint)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from openai import AsyncOpenAI

from .types import AssistantMessage, Message, SystemMessage, UserMessage

if TYPE_CHECKING:
    import httpx


class OpenAIClient:
    """Client for OpenAI-compatible APIs.

    Supports OpenAI, Google Gemini, xAI Grok, and Ollama through their
    OpenAI-compatible endpoints.
    """

    def __init__(
        self,
        model: str,
        api_key: str,
        base_url: str | None = None,
        http_client: "httpx.AsyncClient | None" = None,
    ):
        """Initialize the OpenAI-compatible client.

        Args:
            model: Model identifier (e.g., "gpt-4o", "gemini-2.0-flash").
            api_key: API key for authentication.
            base_url: Optional base URL for non-OpenAI providers.
            http_client: Optional shared httpx client for connection pooling.
        """
        self.model = model
        self._api_key: str | None = api_key
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            http_client=http_client,
        )

    async def create(self, messages: list[Message]) -> str:
        """Send messages to the model and get a response.

        Args:
            messages: List of messages forming the conversation.

        Returns:
            The model's response text.

        Raises:
            openai.APIError: If the API request fails.
        """
        response = await self._client.chat.completions.create(
            model=self.model,
            messages=[self._convert_message(m) for m in messages],
        )

        # Extract content from response
        content = response.choices[0].message.content
        return content if content is not None else ""

    def _convert_message(self, msg: Message) -> dict[str, str]:
        """Convert internal message type to OpenAI format.

        Args:
            msg: Internal message object.

        Returns:
            Dict in OpenAI message format.
        """
        if isinstance(msg, SystemMessage):
            return {"role": "system", "content": msg.content}
        elif isinstance(msg, UserMessage):
            return {"role": "user", "content": msg.content}
        elif isinstance(msg, AssistantMessage):
            return {"role": "assistant", "content": msg.content}
        else:
            # Fallback for any unknown type
            return {"role": "user", "content": str(msg.content)}
