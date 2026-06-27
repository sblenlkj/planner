from dataclasses import dataclass
from uuid import UUID

from telegram_gateway.application.ports.agent_client import AgentClient
from telegram_gateway.application.ports.backend_client import BackendClient
from telegram_gateway.application.ports.conversation_store import ConversationStore
from telegram_gateway.application.ports.telegram_message_sender import (
    TelegramMessageSender,
)
from telegram_gateway.application.ports.telegram_update_deduplicator import (
    TelegramUpdateDeduplicator,
)
from telegram_gateway.application.ports.unit_of_work import UnitOfWork
from telegram_gateway.application.errors import AgentResponseError
from telegram_gateway.domain.models import ConversationMessage, ConversationMessageRole
from telegram_gateway.domain.models import TelegramBinding
from telegram_gateway.logging import get_logger

from .send_agent_message import SendAgentMessage
from .close_agent_session import CloseAgentSession

@dataclass(slots=True)
class IncomingTelegramWebhookMessage:
    update_id: int
    telegram_user_id: int
    telegram_chat_id: int
    text: str
    telegram_username: str | None = None
    telegram_first_name: str | None = None
    telegram_last_name: str | None = None


class HandleTelegramWebhookMessage:
    def __init__(
        self,
        *,
        backend_client: BackendClient,
        agent_client: AgentClient,
        conversation_store: ConversationStore,
        telegram_message_sender: TelegramMessageSender,
        telegram_update_deduplicator: TelegramUpdateDeduplicator,
    ) -> None:
        self._backend_client = backend_client
        self._agent_client = agent_client
        self._conversation_store = conversation_store
        self._telegram_message_sender = telegram_message_sender
        self._telegram_update_deduplicator = telegram_update_deduplicator
        self._log = get_logger(self.__class__.__name__)


        self._send_agent_message = SendAgentMessage(
            agent_client=self._agent_client,
            conversation_store=self._conversation_store,
        )
        self._close_agent_session = CloseAgentSession(
            agent_client=self._agent_client,
            conversation_store=self._conversation_store,
        )

    async def handle(
        self,
        message: IncomingTelegramWebhookMessage,
        uow: UnitOfWork,
    ):
        self._log.info(
            "use_case.started",
            use_case="handle_telegram_webhook_message",
            update_id=message.update_id,
            telegram_user_id=message.telegram_user_id,
            telegram_chat_id=message.telegram_chat_id,
            text_length=len(message.text),
        )

        if not await self._telegram_update_deduplicator.mark_processing_started(
            message.update_id
        ):
            self._log.info(
                "use_case.finished",
                use_case="handle_telegram_webhook_message",
                update_id=message.update_id,
                duplicate=True,
            )
            return False

        async with uow:
            binding = await uow.telegram_bindings.get_by_telegram_user_id(
                telegram_user_id=message.telegram_user_id,
            )

        if binding is None:
            if not self._is_start_message(message.text):
                await self._telegram_message_sender.send_text(
                    telegram_chat_id=message.telegram_chat_id,
                    text="Send /start to create your account and link Telegram.",
                )
                self._log.info(
                    "use_case.finished",
                    use_case="handle_telegram_webhook_message",
                    update_id=message.update_id,
                    binding_exists=False,
                )
                return True

            created_business_user_id = await self._backend_client.create_user(
                password=self._default_password(message.telegram_user_id),
                login=self._build_login(message.telegram_user_id, message.telegram_username),
                name=self._build_name(
                    message.telegram_first_name,
                    message.telegram_last_name,
                    message.telegram_username,
                    message.telegram_user_id,
                ),
                utc_offset_minutes=180,
            )
            binding = await self._create_binding(
                business_user_id=created_business_user_id,
                telegram_user_id=message.telegram_user_id,
                telegram_chat_id=message.telegram_chat_id,
                uow=uow,
            )
            await self._telegram_message_sender.send_text(
                telegram_chat_id=message.telegram_chat_id,
                text="Your account has been created and linked. Send another message to continue.",
            )
            self._log.info(
                "use_case.finished",
                use_case="handle_telegram_webhook_message",
                update_id=message.update_id,
                binding_exists=False,
                business_user_id=str(binding.business_user_id),
            )
            return True

        if message.text == "/close":
            await self._close_agent_session.close(business_user_id=binding.business_user_id)
            assistant_text = "Session is closed."

        else:
            try:
                assistant_text = await self._send_agent_message.send(
                    business_user_id=binding.business_user_id,
                    text=message.text,
                )
            except AgentResponseError as exc:
                self._log.error(
                    "use_case.agent_unavailable",
                    use_case="handle_telegram_webhook_message",
                    update_id=message.update_id,
                    business_user_id=str(binding.business_user_id),
                )
                await self._telegram_message_sender.send_text(
                    telegram_chat_id=binding.telegram_chat_id,
                    text="Sorry, the assistant is temporarily unavailable. Please try again later.",
                )
                self._log.info(
                    "use_case.finished",
                    use_case="handle_telegram_webhook_message",
                    update_id=message.update_id,
                    business_user_id=str(binding.business_user_id),
                    telegram_chat_id=binding.telegram_chat_id,
                    assistant_text_exists=False,
                    agent_error=str(exc),
                )
                return

        if assistant_text is None:
            self._log.info(
                "use_case.finished",
                use_case="handle_telegram_webhook_message",
                update_id=message.update_id,
                assistant_text_exists=False,
            )
            return

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

    async def _create_binding(
        self,
        *,
        business_user_id: UUID,
        telegram_user_id: int,
        telegram_chat_id: int,
        uow: UnitOfWork,
    ) -> TelegramBinding:
        binding = TelegramBinding(
            business_user_id=business_user_id,
            telegram_user_id=telegram_user_id,
            telegram_chat_id=telegram_chat_id,
        )
        async with uow:
            await uow.telegram_bindings.upsert(binding)
            await uow.commit()
        return binding

    def _default_password(self, telegram_user_id: int) -> str:
        return f"telegram-{telegram_user_id}"

    def _build_login(self, telegram_user_id: int, telegram_username: str | None) -> str:
        if telegram_username:
            return telegram_username.lower()
        return f"telegram_{telegram_user_id}"

    def _build_name(
        self,
        telegram_first_name: str | None,
        telegram_last_name: str | None,
        telegram_username: str | None,
        telegram_user_id: int,
    ) -> str:
        parts = [part for part in [telegram_first_name, telegram_last_name] if part]
        if parts:
            return " ".join(parts)
        if telegram_username:
            return telegram_username
        return f"Telegram user {telegram_user_id}"

    def _is_start_message(self, text: str) -> bool:
        normalized = text.strip().lower()
        return normalized == "/start" or normalized.startswith("/start ")
