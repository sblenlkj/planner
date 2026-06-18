from dataclasses import dataclass

from telegram_gateway.application.errors import TelegramBindingNotFoundError
from telegram_gateway.application.ports.agent_client import AgentClient
from telegram_gateway.application.ports.conversation_store import ConversationStore
from telegram_gateway.application.ports.telegram_message_sender import (
    TelegramMessageSender,
)
from telegram_gateway.application.ports.telegram_update_deduplicator import (
    TelegramUpdateDeduplicator,
)
from telegram_gateway.application.ports.unit_of_work import UnitOfWork
from telegram_gateway.domain.models import (
    ConversationMessage,
    ConversationMessageRole,
)
from telegram_gateway.logging import get_logger


@dataclass(slots=True)
class IncomingTelegramWebhookMessage:
    update_id: int
    telegram_user_id: int
    telegram_chat_id: int
    text: str


class HandleTelegramWebhookMessage:
    def __init__(
        self,
        *,
        agent_client: AgentClient,
        conversation_store: ConversationStore,
        telegram_message_sender: TelegramMessageSender,
        update_deduplicator: TelegramUpdateDeduplicator,
    ) -> None:
        self._agent_client = agent_client
        self._conversation_store = conversation_store
        self._telegram_message_sender = telegram_message_sender
        self._update_deduplicator = update_deduplicator
        self._log = get_logger(self.__class__.__name__)

    async def handle(
        self,
        *,
        message: IncomingTelegramWebhookMessage,
        uow: UnitOfWork,
    ) -> bool:
        """Handles incoming Telegram webhook message.

        Returns:
            True  - update was processed.
            False - update was skipped as duplicate.
        """

        self._log.info(
            "use_case.started",
            use_case="handle_telegram_webhook_message",
            update_id=message.update_id,
            telegram_user_id=message.telegram_user_id,
            telegram_chat_id=message.telegram_chat_id,
            text_length=len(message.text),
        )

        can_process = await self._update_deduplicator.mark_processing_started(
            update_id=message.update_id,
        )

        if not can_process:
            self._log.info(
                "use_case.finished",
                use_case="handle_telegram_webhook_message",
                update_id=message.update_id,
                skipped=True,
                reason="duplicate_update",
            )

            return False

        async with uow:
            binding = await uow.telegram_bindings.get_by_telegram_user_id(
                telegram_user_id=message.telegram_user_id,
            )

        if binding is None:
            await self._telegram_message_sender.send_text(
                telegram_chat_id=message.telegram_chat_id,
                text=(
                    "Я пока не знаю, к какому профилю привязан этот Telegram. "
                    "Сначала привяжи Telegram аккаунт в Telegram Gateway."
                ),
            )

            raise TelegramBindingNotFoundError(
                "Telegram binding was not found for "
                f"telegram_user_id={message.telegram_user_id}"
            )

        await self._conversation_store.append_message(
            business_user_id=binding.business_user_id,
            message=ConversationMessage(
                role=ConversationMessageRole.USER,
                content=message.text,
            ),
        )

        messages = await self._conversation_store.get_messages(
            business_user_id=binding.business_user_id,
        )

        assistant_text = await self._agent_client.handle_messages(
            business_user_id=binding.business_user_id,
            messages=messages,
        )

        if assistant_text is None:
            self._log.info(
                "use_case.finished",
                use_case="handle_telegram_webhook_message",
                update_id=message.update_id,
                business_user_id=str(binding.business_user_id),
                assistant_text_exists=False,
            )

            return True

        await self._conversation_store.append_message(
            business_user_id=binding.business_user_id,
            message=ConversationMessage(
                role=ConversationMessageRole.ASSISTANT,
                content=assistant_text,
            ),
        )

        await self._telegram_message_sender.send_text(
            telegram_chat_id=binding.telegram_chat_id,
            text=assistant_text,
        )

        self._log.info(
            "use_case.finished",
            use_case="handle_telegram_webhook_message",
            update_id=message.update_id,
            business_user_id=str(binding.business_user_id),
            telegram_chat_id=binding.telegram_chat_id,
            assistant_text_exists=True,
        )

        return True