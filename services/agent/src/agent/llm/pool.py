from __future__ import annotations

import asyncio
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import AsyncIterator

from .errors import LlmCapacityTimeoutError
from .models import LlmSessionRequest, LlmWorkload
from .session import LlmSession
from .slot import LlmSlot


class LlmProviderPool:
    """In-process pool of exclusive LLM slots.

    This implementation is intentionally for a single FastAPI process. Do not
    run multiple Uvicorn workers with the same physical keys unless this pool is
    replaced by a distributed lease implementation.
    """

    def __init__(
        self,
        slots: list[LlmSlot],
        *,
        acquire_timeout_seconds: float = 30.0,
    ) -> None:
        if not slots:
            raise ValueError("LlmProviderPool requires at least one slot")

        self._all_slots = {slot.slot_id: slot for slot in slots}
        self._available: dict[LlmWorkload, asyncio.Queue[LlmSlot]] = defaultdict(asyncio.Queue)
        self._slot_workloads: dict[str, set[LlmWorkload]] = {}
        self._acquire_timeout_seconds = acquire_timeout_seconds

        for slot in slots:
            if not slot.workloads:
                raise ValueError(f"Slot {slot.slot_id!r} must support at least one workload")
            self._slot_workloads[slot.slot_id] = set(slot.workloads)
            for workload in slot.workloads:
                self._available[workload].put_nowait(slot)

    @asynccontextmanager
    async def session(self, request: LlmSessionRequest) -> AsyncIterator[LlmSession]:
        slot = await self.acquire(request.workload)
        session = LlmSession(slot=slot, pool=self, request=request)
        try:
            yield session
        finally:
            await session.release()

    async def acquire(self, workload: LlmWorkload) -> LlmSlot:
        queue = self._available.get(workload)
        if queue is None:
            raise LlmCapacityTimeoutError(f"No LLM slots configured for workload {workload}")

        deadline = asyncio.get_running_loop().time() + self._acquire_timeout_seconds
        while True:
            timeout = max(0.0, deadline - asyncio.get_running_loop().time())
            if timeout == 0.0:
                raise LlmCapacityTimeoutError(
                    f"Timed out acquiring LLM slot for workload {workload}"
                )
            try:
                slot = await asyncio.wait_for(queue.get(), timeout=timeout)
            except TimeoutError as exc:
                raise LlmCapacityTimeoutError(
                    f"Timed out acquiring LLM slot for workload {workload}"
                ) from exc

            if slot.is_in_cooldown():
                # Put the slot back and avoid a tight loop.
                await queue.put(slot)
                await asyncio.sleep(0.1)
                continue
            return slot

    async def release(self, slot: LlmSlot) -> None:
        workloads = self._slot_workloads.get(slot.slot_id)
        if workloads is None:
            raise ValueError(f"Unknown LLM slot: {slot.slot_id}")
        for workload in workloads:
            await self._available[workload].put(slot)

    def configured_slots(self) -> list[LlmSlot]:
        return list(self._all_slots.values())
