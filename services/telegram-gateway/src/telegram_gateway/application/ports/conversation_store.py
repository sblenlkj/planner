from uuid import UUID

from telegram_gateway.domain.models import ConversationMessage


class ConversationStore:
    async def append_message(
        self,
        business_user_id: UUID,
        message: ConversationMessage,
    ) -> list[ConversationMessage]:
        raise NotImplementedError

    async def get_messages(
        self,
        business_user_id: UUID,
    ) -> list[ConversationMessage]:
        raise NotImplementedError

    async def clear_messages(
        self,
        business_user_id: UUID,
    ) -> None:
        raise NotImplementedError
