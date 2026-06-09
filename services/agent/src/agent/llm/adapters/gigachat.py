from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_gigachat.chat_models import GigaChat

from ..models import LlmMessage, LlmRequest, LlmResponse, LlmUsage
from ..ports import LangChainChatModelProviderPort, LlmProviderPort


@dataclass(frozen=True, slots=True)
class GigaChatProviderConfig:
    credentials: str
    model: str = "GigaChat-Pro"
    scope: str = "GIGACHAT_API_PERS"
    verify_ssl_certs: bool = False
    temperature: float | None = None
    timeout: float | None = None


class GigaChatProvider(LlmProviderPort, LangChainChatModelProviderPort):
    """GigaChat/LangChain adapter hidden behind the LLM provider port."""

    provider_name = "gigachat"

    def __init__(self, config: GigaChatProviderConfig) -> None:
        self._config = config
        kwargs: dict[str, Any] = {
            "credentials": config.credentials,
            "scope": config.scope,
            "model": config.model,
            "verify_ssl_certs": config.verify_ssl_certs,
        }
        if config.temperature is not None:
            kwargs["temperature"] = config.temperature
        if config.timeout is not None:
            kwargs["timeout"] = config.timeout
        self._chat_model = GigaChat(**kwargs)

    @property
    def model_name(self) -> str:
        return self._config.model

    def get_langchain_chat_model(self) -> Any:
        return self._chat_model

    async def complete(self, request: LlmRequest) -> LlmResponse:
        messages = [_to_langchain_message(message) for message in request.messages]
        model = self._chat_model

        # LangChain chat models normally expose ainvoke. The fallback keeps the
        # adapter usable with sync-only test doubles.
        if hasattr(model, "ainvoke"):
            raw = await model.ainvoke(messages)
        else:
            raw = await asyncio.to_thread(model.invoke, messages)

        content = getattr(raw, "content", str(raw))
        usage = _extract_usage(raw)
        return LlmResponse(content=content, usage=usage, raw=raw)


def _to_langchain_message(message: LlmMessage) -> BaseMessage:
    if message.role == "system":
        return SystemMessage(content=message.content)
    if message.role == "user":
        return HumanMessage(content=message.content)
    if message.role == "assistant":
        return AIMessage(content=message.content)
    if message.role == "tool":
        return ToolMessage(content=message.content, tool_call_id=message.name or "tool")
    raise ValueError(f"Unsupported LLM message role: {message.role}")


def _extract_usage(raw: Any) -> LlmUsage | None:
    usage_metadata = getattr(raw, "usage_metadata", None)
    if isinstance(usage_metadata, dict):
        return LlmUsage(
            input_tokens=usage_metadata.get("input_tokens"),
            output_tokens=usage_metadata.get("output_tokens"),
            total_tokens=usage_metadata.get("total_tokens"),
            cached_input_tokens=usage_metadata.get("cached_input_tokens"),
            raw=usage_metadata,
        )

    response_metadata = getattr(raw, "response_metadata", None)
    token_usage = None
    if isinstance(response_metadata, dict):
        token_usage = response_metadata.get("token_usage") or response_metadata.get("usage")
    if isinstance(token_usage, dict):
        return LlmUsage(
            input_tokens=token_usage.get("prompt_tokens") or token_usage.get("input_tokens"),
            output_tokens=token_usage.get("completion_tokens") or token_usage.get("output_tokens"),
            total_tokens=token_usage.get("total_tokens"),
            cached_input_tokens=token_usage.get("cached_input_tokens"),
            raw=token_usage,
        )
    return None
