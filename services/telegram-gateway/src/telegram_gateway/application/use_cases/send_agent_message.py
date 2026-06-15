from uuid import UUID

from telegram_gateway.application.errors import TelegramBindingNotFoundError
from telegram_gateway.application.ports.agent_client import AgentClient
from telegram_gateway.application.ports.conversation_store import ConversationStore
from telegram_gateway.application.ports.telegram_message_sender import (
    TelegramMessageSender,
)
from telegram_gateway.application.ports.unit_of_work import UnitOfWork
from telegram_gateway.domain.models import ConversationMessage, ConversationMessageRole
from telegram_gateway.logging import get_logger


class SendAgentMessage:
    def __init__(
        self,
        *,
        agent_client: AgentClient,
        conversation_store: ConversationStore,
    ) -> None:
        self._agent_client = agent_client
        self._conversation_store = conversation_store
        self._log = get_logger(self.__class__.__name__)

    async def send(
        self,
        *,
        business_user_id: UUID,
        text: str,
        uow: UnitOfWork,
    ) -> str | None:
        self._log.info(
            "use_case.started",
            use_case="send_agent_message",
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

        messages = await self._conversation_store.append_message(
            business_user_id=business_user_id,
            message=ConversationMessage(
                role=ConversationMessageRole.USER,
                content=text,
            ),
        )

        assistant_text = await self._agent_client.handle_messages(
            business_user_id=business_user_id,
            messages=messages,
        )

        if assistant_text is None:
            self._log.info(
                "use_case.finished",
                use_case="send_agent_message",
                business_user_id=str(business_user_id),
                assistant_text_exists=False,
            )
            return None

        await self._conversation_store.append_message(
            business_user_id=business_user_id,
            message=ConversationMessage(
                role=ConversationMessageRole.ASSISTANT,
                content=assistant_text,
            ),
        )

        self._log.info(
            "use_case.finished",
            use_case="send_agent_message",
            business_user_id=str(business_user_id),
            telegram_chat_id=binding.telegram_chat_id,
            assistant_text_exists=True,
        )

        return assistant_text
