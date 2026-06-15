from uuid import UUID

from telegram_gateway.application.ports.conversation_store import ConversationStore
from telegram_gateway.domain.models import ConversationMessage
from telegram_gateway.logging import get_logger


class GetAgentSession:
    def __init__(
        self,
        *,
        conversation_store: ConversationStore,
    ) -> None:
        self._conversation_store = conversation_store
        self._log = get_logger(self.__class__.__name__)

    async def get(
        self,
        *,
        business_user_id: UUID,
    ) -> list[ConversationMessage]:
        self._log.info(
            "use_case.started",
            use_case="get_agent_session",
            business_user_id=str(business_user_id),
        )

        messages = await self._conversation_store.get_messages(
            business_user_id=business_user_id,
        )

        self._log.info(
            "use_case.finished",
            use_case="get_agent_session",
            business_user_id=str(business_user_id),
            messages_count=len(messages),
        )

        return messages