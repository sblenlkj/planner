from __future__ import annotations

from dataclasses import dataclass, field
from time import monotonic

from .models import LlmWorkload
from .ports import LlmProviderPort


@dataclass(slots=True)
class LlmSlot:
    """Exclusive execution slot for one provider client/credential.

    In the current design one slot means concurrency=1 for one provider client.
    A slot is reserved for an execution scope: agent run, workflow run, or
    homogeneous batch drain.
    """

    slot_id: str
    provider: LlmProviderPort
    workloads: set[LlmWorkload]
    label: str | None = None
    cooldown_until: float = 0.0
    metadata: dict[str, str] = field(default_factory=dict)

    def supports(self, workload: LlmWorkload) -> bool:
        return workload in self.workloads

    def is_in_cooldown(self) -> bool:
        return monotonic() < self.cooldown_until

    def put_on_cooldown(self, seconds: float) -> None:
        self.cooldown_until = monotonic() + seconds
