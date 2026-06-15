from uuid import UUID

from telegram_gateway.application.errors import TelegramBindingNotFoundError
from telegram_gateway.application.ports.conversation_store import ConversationStore
from telegram_gateway.application.ports.telegram_message_sender import (
    TelegramMessageSender,
)
from telegram_gateway.application.ports.unit_of_work import UnitOfWork
from telegram_gateway.domain.models import ConversationMessage, ConversationMessageRole
from telegram_gateway.logging import get_logger


class SendTelegramNotification:
    def __init__(
        self,
        *,
        conversation_store: ConversationStore,
        telegram_message_sender: TelegramMessageSender,
    ) -> None:
        self._conversation_store = conversation_store
        self._telegram_message_sender = telegram_message_sender
        self._log = get_logger(self.__class__.__name__)

    async def send(
        self,
        *,
        business_user_id: UUID,
        text: str,
        uow: UnitOfWork,
    ) -> None:
        self._log.info(
            "use_case.started",
            use_case="send_telegram_notification",
            business_user_id=str(business_user_id),
            text_length=len(text),
        )

        async with uow:
            binding = await uow.telegram_bindings.get_by_business_user_id(
                business_user_id=business_user_id,
            )

        if binding is None:
            raise TelegramBindingNotFoundError(
                f"Telegram binding was not found for business_user_id={business_user_id}"
            )

        await self._conversation_store.append_message(
            business_user_id=business_user_id,
            message=ConversationMessage(
                role=ConversationMessageRole.ASSISTANT,
                content=text,
            ),
        )

        await self._telegram_message_sender.send_text(
            telegram_chat_id=binding.telegram_chat_id,
            text=text,
        )

        self._log.info(
            "use_case.finished",
            use_case="send_telegram_notification",
            business_user_id=str(business_user_id),
            telegram_chat_id=binding.telegram_chat_id,
        )
