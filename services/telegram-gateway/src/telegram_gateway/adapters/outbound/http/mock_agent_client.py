import asyncio
from uuid import UUID

from telegram_gateway.application.ports.agent_client import AgentClient
from telegram_gateway.domain.models import ConversationMessage


class MockAgentClient(AgentClient):
    def __init__(self, sleep_seconds: float = 10.0) -> None:
        self._sleep_seconds = sleep_seconds

    async def handle_onboarding_messages(
        self,
        business_user_id: UUID,
        messages: list[ConversationMessage],
    ) -> str | None:
        await asyncio.sleep(self._sleep_seconds)
        last_user_message = _find_last_user_message(messages)

        if last_user_message is None:
            return "Mock onboarding agent: получил пустой диалог."

        return (
            "Mock onboarding agent: я помогаю заполнить базовый профиль. "
            f"Последнее сообщение пользователя: {last_user_message.content}"
        )

    async def handle_messages(
        self,
        business_user_id: UUID,
        messages: list[ConversationMessage],
    ) -> str | None:
        await asyncio.sleep(self._sleep_seconds)
        last_user_message = _find_last_user_message(messages)

        if last_user_message is None:
            return "Mock main agent: получил пустой диалог."

        return (
            "Mock main agent: обработал сообщение основного пользователя. "
            f"Последнее сообщение: {last_user_message.content}"
        )


def _find_last_user_message(
    messages: list[ConversationMessage],
) -> ConversationMessage | None:
    for message in reversed(messages):
        if message.role.value == "user":
            return message
    return None
