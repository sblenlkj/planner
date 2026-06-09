from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from .models import LlmRequest, LlmResponse


@runtime_checkable
class LlmProviderPort(Protocol):
    """Provider-neutral LLM client boundary.

    The orchestrator and agents depend on this protocol, not on GigaChat,
    LangChain, HTTP clients, credentials, or provider SDK details.
    """

    provider_name: str
    model_name: str

    async def complete(self, request: LlmRequest) -> LlmResponse:
        ...


@runtime_checkable
class LangChainChatModelProviderPort(Protocol):
    """Optional capability for LangGraph/LangChain integration."""

    def get_langchain_chat_model(self) -> Any:
        """Return a LangChain-compatible chat model, for example BaseChatModel."""
        ...
