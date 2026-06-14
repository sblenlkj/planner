from uuid import UUID

from telegram_gateway.application.ports.unit_of_work import UnitOfWork
from telegram_gateway.application.services.binding_service import BindingService
from telegram_gateway.application.services.conversation_service import ConversationService
from telegram_gateway.domain.models import TelegramBinding


class CloseTelegramSession:
    def __init__(
        self,
        *,
        binding_service: BindingService,
        conversation_service: ConversationService,
    ) -> None:
        self._binding_service = binding_service
        self._conversation_service = conversation_service

    async def close_by_business_user(
        self,
        *,
        business_user_id: UUID,
        uow: UnitOfWork,
    ) -> bool:
        async with uow:
            binding = await self._binding_service.get_by_business_user_id(
                business_user_id=business_user_id,
                telegram_bindings=uow.telegram_bindings,
            )

        return await self.close_by_binding(binding=binding)

    async def close_by_binding(
        self,
        *,
        binding: TelegramBinding,
    ) -> bool:
        return await self._conversation_service.close(
            business_user_id=binding.business_user_id,
            telegram_chat_id=binding.telegram_chat_id,
        )
