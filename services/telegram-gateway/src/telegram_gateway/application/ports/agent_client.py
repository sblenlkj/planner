from datetime import datetime
from typing import Protocol
from uuid import UUID

from telegram_gateway.domain.models import ConversationMessage


class AgentClient(Protocol):
    async def handle_messages(
        self,
        business_user_id: UUID,
        messages: list[ConversationMessage],
    ) -> str | None:
        ...

    async def close_session(
        self,
        business_user_id: UUID,
        closed_at: datetime,
        messages: list[ConversationMessage],
    ) -> None:
        ...
