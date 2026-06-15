from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any


@dataclass
class LlmSlotMetrics:
    total_slots: int = 0
    in_use_slots: int = 0
    acquire_waiters: int = 0

    acquire_total: int = 0
    release_total: int = 0
    acquire_timeout_total: int = 0

    acquire_wait_seconds_total: float = 0.0
    run_seconds_total: float = 0.0

    def set_total_slots(self, value: int) -> None:
        self.total_slots = value

    def on_wait_started(self) -> float:
        self.acquire_waiters += 1
        return time.monotonic()

    def on_acquired(self, wait_started_at: float) -> float:
        now = time.monotonic()
        waited_seconds = now - wait_started_at

        self.acquire_waiters = max(0, self.acquire_waiters - 1)
        self.acquire_total += 1
        self.in_use_slots += 1
        self.acquire_wait_seconds_total += waited_seconds

        return now

    def on_timeout(self) -> None:
        self.acquire_waiters = max(0, self.acquire_waiters - 1)
        self.acquire_timeout_total += 1

    def on_released(self, run_started_at: float) -> None:
        run_seconds = time.monotonic() - run_started_at

        self.release_total += 1
        self.in_use_slots = max(0, self.in_use_slots - 1)
        self.run_seconds_total += run_seconds

    def snapshot(self) -> dict[str, Any]:
        available = self.total_slots - self.in_use_slots

        average_wait_seconds = (
            self.acquire_wait_seconds_total / self.acquire_total
            if self.acquire_total > 0
            else 0.0
        )

        average_run_seconds = (
            self.run_seconds_total / self.release_total
            if self.release_total > 0
            else 0.0
        )

        utilization = (
            self.in_use_slots / self.total_slots
            if self.total_slots > 0
            else 0.0
        )

        return {
            "llm_slots_total": self.total_slots,
            "llm_slots_in_use": self.in_use_slots,
            "llm_slots_available": available,
            "llm_slot_utilization": round(utilization, 6),
            "llm_slot_acquire_waiters": self.acquire_waiters,
            "llm_slot_acquire_total": self.acquire_total,
            "llm_slot_release_total": self.release_total,
            "llm_slot_acquire_timeout_total": self.acquire_timeout_total,
            "llm_slot_acquire_wait_seconds_total": round(self.acquire_wait_seconds_total, 6),
            "llm_slot_run_seconds_total": round(self.run_seconds_total, 6),
            "llm_slot_average_wait_seconds": round(average_wait_seconds, 6),
            "llm_slot_average_run_seconds": round(average_run_seconds, 6),
        }


llm_slot_metrics = LlmSlotMetrics()