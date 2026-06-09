from __future__ import annotations

from dataclasses import dataclass, field
from time import monotonic
from typing import TYPE_CHECKING, Any

from .errors import LlmSessionExpiredError, UnsupportedProviderFeatureError
from .models import LlmRequest, LlmResponse, LlmSessionRequest
from .ports import LangChainChatModelProviderPort
from .slot import LlmSlot

if TYPE_CHECKING:
    from .pool import LlmProviderPool


@dataclass(slots=True)
class LlmSessionStats:
    llm_calls: int = 0
    started_at_monotonic: float = field(default_factory=monotonic)

    @property
    def duration_seconds(self) -> float:
        return monotonic() - self.started_at_monotonic


class LlmSession:
    """Reserved access to one LLM slot.

    The session is intentionally broader than a single provider call. It can
    cover a LangGraph agent run or a batch chunk that reuses one stable prompt
    and toolset across many dynamic user payloads.
    """

    def __init__(
        self,
        *,
        slot: LlmSlot,
        pool: LlmProviderPool,
        request: LlmSessionRequest,
    ) -> None:
        self._slot = slot
        self._pool = pool
        self.request = request
        self.stats = LlmSessionStats()
        self._released = False

    @property
    def slot_id(self) -> str:
        return self._slot.slot_id

    @property
    def provider_name(self) -> str:
        return self._slot.provider.provider_name

    @property
    def model_name(self) -> str:
        return self._slot.provider.model_name

    @property
    def provider(self):
        return self._slot.provider

    async def complete(self, request: LlmRequest) -> LlmResponse:
        self._ensure_alive()
        self.stats.llm_calls += 1
        return await self._slot.provider.complete(request)

    def require_langchain_chat_model(self) -> Any:
        """Return a reserved LangChain chat model for LangGraph agents.

        The returned object must be used only while this session is active.
        """

        provider = self._slot.provider
        if not isinstance(provider, LangChainChatModelProviderPort):
            raise UnsupportedProviderFeatureError(
                f"Provider {provider.provider_name!r} does not expose LangChain chat model"
            )
        self._ensure_alive()
        return provider.get_langchain_chat_model()

    async def release(self) -> None:
        if not self._released:
            self._released = True
            await self._pool.release(self._slot)

    async def __aenter__(self) -> "LlmSession":
        self._ensure_alive()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.release()

    def _ensure_alive(self) -> None:
        if self._released:
            raise LlmSessionExpiredError("LLM session has already been released")
        max_duration = self.request.max_duration_seconds
        if max_duration is not None and self.stats.duration_seconds > max_duration:
            raise LlmSessionExpiredError(
                f"LLM session exceeded max duration: {max_duration}s"
            )
