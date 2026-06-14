from uuid import UUID

from telegram_gateway.application.ports.telegram_message_sender import TelegramMessageSender
from telegram_gateway.application.ports.unit_of_work import UnitOfWork
from telegram_gateway.application.services.binding_service import BindingService
from telegram_gateway.application.services.conversation_service import ConversationService


class SendBusinessMessage:
    def __init__(
        self,
        *,
        binding_service: BindingService,
        conversation_service: ConversationService,
        telegram_message_sender: TelegramMessageSender,
    ) -> None:
        self._binding_service = binding_service
        self._conversation_service = conversation_service
        self._telegram_message_sender = telegram_message_sender

    async def send_to_business_user(
        self,
        *,
        business_user_id: UUID,
        text: str,
        uow: UnitOfWork,
    ) -> None:
        async with uow:
            binding = await self._binding_service.get_by_business_user_id(
                business_user_id=business_user_id,
                telegram_bindings=uow.telegram_bindings,
            )

        await self._conversation_service.append_assistant_message(
            telegram_chat_id=binding.telegram_chat_id,
            text=text,
        )

        await self._telegram_message_sender.send_text(
            telegram_chat_id=binding.telegram_chat_id,
            text=text,
        )
