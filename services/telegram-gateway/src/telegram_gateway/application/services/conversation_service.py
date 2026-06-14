from datetime import datetime, timezone
from uuid import UUID, uuid4

from telegram_gateway.application.ports.backend_client import BackendClient
from telegram_gateway.application.ports.closed_session_publisher import (
    ClosedSessionPublisher,
)
from telegram_gateway.application.ports.conversation_store import ConversationStore
from telegram_gateway.domain.events import ClosedSessionEvent
from telegram_gateway.domain.models import ConversationMessage, ConversationMessageRole


class ConversationService:
    def __init__(
        self,
        *,
        conversation_store: ConversationStore,
        closed_session_publisher: ClosedSessionPublisher,
        backend_client: BackendClient,
    ) -> None:
        self._conversation_store = conversation_store
        self._closed_session_publisher = closed_session_publisher
        self._backend_client = backend_client

    async def append_user_message(
        self,
        *,
        telegram_chat_id: int,
        text: str,
    ) -> list[ConversationMessage]:
        await self._conversation_store.append_message(
            telegram_chat_id=telegram_chat_id,
            message=ConversationMessage(
                role=ConversationMessageRole.USER,
                content=text,
            ),
        )
        return await self._conversation_store.get_messages(
            telegram_chat_id=telegram_chat_id,
        )

    async def append_assistant_message(
        self,
        *,
        telegram_chat_id: int,
        text: str,
    ) -> None:
        await self._conversation_store.append_message(
            telegram_chat_id=telegram_chat_id,
            message=ConversationMessage(
                role=ConversationMessageRole.ASSISTANT,
                content=text,
            ),
        )

    async def get_messages(
        self,
        *,
        telegram_chat_id: int,
    ) -> list[ConversationMessage]:
        return await self._conversation_store.get_messages(
            telegram_chat_id=telegram_chat_id,
        )

    async def close(
        self,
        *,
        business_user_id: UUID,
        telegram_chat_id: int,
    ) -> bool:
        messages = await self._conversation_store.get_messages(
            telegram_chat_id=telegram_chat_id,
        )

        if not messages:
            return False

        closed_at = datetime.now(timezone.utc)

        await self._closed_session_publisher.publish_closed_session(
            ClosedSessionEvent(
                event_id=uuid4(),
                business_user_id=business_user_id,
                telegram_chat_id=telegram_chat_id,
                closed_at=closed_at,
                messages=messages,
            )
        )

        await self._conversation_store.clear_messages(
            telegram_chat_id=telegram_chat_id,
        )

        await self._backend_client.update_user_last_session_at(
            business_user_id=business_user_id,
            last_session_at=closed_at,
        )

        return True

    async def clear(
        self,
        *,
        telegram_chat_id: int,
    ) -> None:
        await self._conversation_store.clear_messages(
            telegram_chat_id=telegram_chat_id,
        )