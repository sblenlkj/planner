from datetime import date
from uuid import UUID
from telegram_gateway.logging import get_logger

from telegram_gateway.application.ports.agent_client import AgentClient, OnboardingAgentResponse
from telegram_gateway.application.ports.backend_client import BackendClient, UserRuntimeStatus
from telegram_gateway.application.ports.runtime_status_cache import RuntimeStatusCache
from telegram_gateway.application.ports.telegram_message_sender import TelegramMessageSender
from telegram_gateway.application.ports.unit_of_work import UnitOfWork
from telegram_gateway.application.run_with_typing_indicator import run_with_typing_indicator
from telegram_gateway.application.services.binding_service import BindingService
from telegram_gateway.application.services.conversation_service import ConversationService
from telegram_gateway.domain.models import TelegramIncomingMessage
from telegram_gateway.application.errors import EmptyTelegramMessageError

class HandleTelegramMessage:
    def __init__(
        self,
        *,
        agent_client: AgentClient,
        backend_client: BackendClient,
        telegram_message_sender: TelegramMessageSender,
        binding_service: BindingService,
        conversation_service: ConversationService,
        runtime_status_cache: RuntimeStatusCache,
        close_commands: set[str] | None = None,
        close_confirmation_text: str = "Сессия закрыта.",
    ) -> None:
        self._agent_client = agent_client
        self._backend_client = backend_client
        self._telegram_message_sender = telegram_message_sender
        self._binding_service = binding_service
        self._conversation_service = conversation_service
        self._runtime_status_cache = runtime_status_cache
        self._close_commands = close_commands or {
            "/close",
            "/end",
            "закрыть сессию",
            "закрой сессию",
        }
        self._close_confirmation_text = close_confirmation_text
        self._log = get_logger(self.__class__.__name__)

    async def handle(
        self,
        *,
        message: TelegramIncomingMessage,
        uow: UnitOfWork,
    ) -> None:
        self._log.info(
            "use_case.started",
            use_case="handle_telegram_message",
            telegram_user_id=message.telegram_user_id,
            telegram_chat_id=message.telegram_chat_id,
            text=message.text,
        )

        text = message.text.strip()

        if not text:
            raise EmptyTelegramMessageError("Telegram message text is empty.")

        async with uow:
            resolution = await self._binding_service.ensure_for_telegram_user(
                telegram_user_id=message.telegram_user_id,
                telegram_chat_id=message.telegram_chat_id,
                telegram_bindings=uow.telegram_bindings,
            )
            if resolution.created:
                await uow.commit()

        binding = resolution.binding

        if self._is_close_command(text):
            closed = await self._conversation_service.close(
                business_user_id=binding.business_user_id,
                telegram_chat_id=binding.telegram_chat_id,
            )
            await self._telegram_message_sender.send_text(
                telegram_chat_id=binding.telegram_chat_id,
                text=self._close_confirmation_text
                if closed
                else "Открытой сессии нет.",
            )
            return

        messages = await self._conversation_service.append_user_message(
            telegram_chat_id=binding.telegram_chat_id,
            text=text,
        )

        status = await self._get_runtime_status(binding.business_user_id)

        if status == UserRuntimeStatus.NOT_READY:
            onboarding_response = await run_with_typing_indicator(
                telegram_chat_id=binding.telegram_chat_id,
                telegram_message_sender=self._telegram_message_sender,
                operation=self._agent_client.handle_onboarding_messages(
                    business_user_id=binding.business_user_id,
                    messages=messages,
                ),
            )

            if not isinstance(onboarding_response, OnboardingAgentResponse): 
                raise TypeError("AgentClient.handle_onboarding_messages returned invalid response.")

            assistant_text = onboarding_response.assistant_text

        if onboarding_response.user_is_ready:
            await self._backend_client.update_user_runtime_status(
                business_user_id=binding.business_user_id,
                status=UserRuntimeStatus.READY,
            )

            await self._runtime_status_cache.set_status(
                business_user_id=binding.business_user_id,
                status=UserRuntimeStatus.READY,
            )

            await self._backend_client.generate_day_schedule(
                business_user_id=binding.business_user_id,
                day=date.today(),
            )

            await self._conversation_service.clear(
                telegram_chat_id=binding.telegram_chat_id,
            )

            ready_text = (
                onboarding_response.assistant_text
                or "Готово. Я запустил генерацию твоего дня. Возвращайся примерно через 15 минут — всё будет готово."
            )

            ready_text = ready_text.strip()

            await self._conversation_service.append_assistant_message(
                telegram_chat_id=binding.telegram_chat_id,
                text=ready_text,
            )

            await self._telegram_message_sender.send_text(
                telegram_chat_id=binding.telegram_chat_id,
                text=ready_text,
            )

            return
        else:
            assistant_text = await run_with_typing_indicator(
                telegram_chat_id=binding.telegram_chat_id,
                telegram_message_sender=self._telegram_message_sender,
                operation=self._agent_client.handle_messages(
                    business_user_id=binding.business_user_id,
                    messages=messages,
                ),
            )

        if assistant_text is None or not assistant_text.strip():
            return

        assistant_text = assistant_text.strip()

        await self._conversation_service.append_assistant_message(
            telegram_chat_id=binding.telegram_chat_id,
            text=assistant_text,
        )

        await self._telegram_message_sender.send_text(
            telegram_chat_id=binding.telegram_chat_id,
            text=assistant_text,
        )

    async def _get_runtime_status(
        self,
        business_user_id: UUID,
    ) -> UserRuntimeStatus:
        status = await self._runtime_status_cache.get_status(business_user_id)

        if status is not None:
            return status

        status = await self._backend_client.get_user_runtime_status(business_user_id)
        await self._runtime_status_cache.set_status(business_user_id, status)
        return status

    def _is_close_command(self, text: str) -> bool:
        return text.strip().lower() in self._close_commands
