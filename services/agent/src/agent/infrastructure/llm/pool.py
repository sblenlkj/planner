from __future__ import annotations

import asyncio
import time
from contextlib import asynccontextmanager
from typing import AsyncIterator, Iterable

from .adapters import GigaChatConnectionFactory
from .slot import AcquiredLlmSlot, LlmSlot
from agent.core.settings import LlmModelKind, Settings

from agent.infrastructure.observability.metrics import llm_slot_metrics

class LlmSlotPool:
    def __init__(
        self,
        *,
        slots: Iterable[LlmSlot],
        connection_factory: GigaChatConnectionFactory,
        acquire_timeout_seconds: float | None = None,
    ) -> None:
        slot_list = list(slots)
        if not slot_list:
            raise ValueError("LlmSlotPool requires at least one slot.")

        self._queue: asyncio.Queue[LlmSlot] = asyncio.Queue()
        self._connection_factory = connection_factory
        self._acquire_timeout_seconds = acquire_timeout_seconds

        llm_slot_metrics.set_total_slots(len(slot_list))

        for slot in slot_list:
            self._queue.put_nowait(slot)

    @classmethod
    def from_settings(cls, settings: Settings) -> "LlmSlotPool":
        slots = [
            LlmSlot(
                slot_id=f"gigachat-{index}",
                credentials=credentials,
                strong_model=settings.llm_strong_model,
                weak_model=settings.llm_weak_model,
                scope=settings.llm_gigachat_scope,
                verify_ssl_certs=settings.llm_gigachat_verify_ssl_certs,
            )
            for index, credentials in enumerate(
                settings.get_llm_credentials(),
                start=1,
            )
        ]

        return cls(
            slots=slots,
            connection_factory=GigaChatConnectionFactory(),
            acquire_timeout_seconds=settings.llm_acquire_timeout_seconds,
        )

    @asynccontextmanager
    async def acquire(
        self,
        *,
        model_kind: LlmModelKind,
    ) -> AsyncIterator[AcquiredLlmSlot]:
        wait_started_at = llm_slot_metrics.on_wait_started()

        slot: LlmSlot | None = None
        acquired_slot: AcquiredLlmSlot | None = None
        run_started_at: float | None = None

        try:
            slot = await self._acquire_slot()

            run_started_at = llm_slot_metrics.on_acquired(wait_started_at)

            acquired_slot = slot.connect(
                model_kind=model_kind,
                factory=self._connection_factory,
            )

            yield acquired_slot

        except TimeoutError:
            llm_slot_metrics.on_timeout()
            raise

        finally:
            if acquired_slot is not None:
                acquired_slot.close()

            if run_started_at is not None:
                llm_slot_metrics.on_released(run_started_at)

            if slot is not None:
                self._queue.put_nowait(slot)

    async def _acquire_slot(self) -> LlmSlot:
        if self._acquire_timeout_seconds is None:
            return await self._queue.get()

        try:
            return await asyncio.wait_for(
                self._queue.get(),
                timeout=self._acquire_timeout_seconds,
            )
        except TimeoutError as exc:
            raise TimeoutError(
                f"No LLM slot became available within "
                f"{self._acquire_timeout_seconds} seconds."
            ) from exc