from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, kw_only=True, slots=True)
class CloseConversationResult:
    user_id: UUID
    closed: bool
    reason: str | None = None


class TelegramGatewayPort(Protocol):
    async def send_message(
        self,
        *,
        user_id: UUID,
        text: str,
    ) -> None:
        raise NotImplementedError

    async def close_conversation(
        self,
        *,
        user_id: UUID,
    ) -> CloseConversationResult:
        raise NotImplementedError