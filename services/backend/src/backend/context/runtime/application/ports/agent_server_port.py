# backend/context/runtime/application/ports/agent_server_port.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from typing import Protocol
from uuid import UUID


class MorningBriefingStatus(StrEnum):
    READY = "ready"
    NOT_READY = "not_ready"
    ERROR = "error"


@dataclass(frozen=True, kw_only=True, slots=True)
class MorningBriefingResult:
    status: MorningBriefingStatus
    text: str | None = None
    reason: str | None = None


class AgentServerPort(Protocol):
    async def run_morning_briefing(
        self,
        *,
        user_id: UUID,
        day: date,
    ) -> MorningBriefingResult:
        raise NotImplementedError