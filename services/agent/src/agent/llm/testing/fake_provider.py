from __future__ import annotations

import asyncio
from dataclasses import dataclass

from ..models import LlmRequest, LlmResponse
from ..ports import LlmProviderPort


@dataclass(slots=True)
class FakeLlmProvider(LlmProviderPort):
    provider_name: str = "fake"
    model_name: str = "fake-model"
    delay_seconds: float = 0.0
    prefix: str = "fake"

    async def complete(self, request: LlmRequest) -> LlmResponse:
        if self.delay_seconds:
            await asyncio.sleep(self.delay_seconds)
        last = request.messages[-1].content if request.messages else ""
        return LlmResponse(content=f"{self.prefix}: {last}")
