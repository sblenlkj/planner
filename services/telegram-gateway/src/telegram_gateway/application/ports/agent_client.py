from datetime import datetime
from uuid import UUID

from telegram_gateway.domain.models import ConversationMessage


class AgentClient:
    async def handle_messages(
        self,
        business_user_id: UUID,
        messages: list[ConversationMessage],
    ) -> str | None:
        raise NotImplementedError

    async def close_session(
        self,
        business_user_id: UUID,
        closed_at: datetime,
        messages: list[ConversationMessage],
    ) -> None:
        raise NotImplementedError
