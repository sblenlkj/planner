from uuid import UUID

from telegram_gateway.application.ports.unit_of_work import UnitOfWork
from telegram_gateway.domain.models import TelegramBinding
from telegram_gateway.logging import get_logger


class AttachTelegram:
    def __init__(self) -> None:
        self._log = get_logger(self.__class__.__name__)

    async def attach(
        self,
        *,
        business_user_id: UUID,
        telegram_user_id: int,
        telegram_chat_id: int,
        uow: UnitOfWork,
    ) -> None:
        self._log.info(
            "use_case.started",
            use_case="attach_telegram",
            business_user_id=str(business_user_id),
            telegram_user_id=telegram_user_id,
            telegram_chat_id=telegram_chat_id,
        )

        binding = TelegramBinding(
            business_user_id=business_user_id,
            telegram_user_id=telegram_user_id,
            telegram_chat_id=telegram_chat_id,
        )

        async with uow:
            await uow.telegram_bindings.upsert(binding)
            await uow.commit()

        self._log.info(
            "use_case.finished",
            use_case="attach_telegram",
            business_user_id=str(business_user_id),
            telegram_user_id=telegram_user_id,
            telegram_chat_id=telegram_chat_id,
        )
