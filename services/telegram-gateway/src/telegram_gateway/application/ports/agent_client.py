from typing import Protocol
from uuid import UUID
from dataclasses import dataclass

from telegram_gateway.domain.models import ConversationMessage

@dataclass(slots=True)
class OnboardingAgentResponse:
    assistant_text: str | None
    user_is_ready: bool

class AgentClient(Protocol):
    async def handle_onboarding_messages(
        self,
        business_user_id: UUID,
        messages: list[ConversationMessage],
    ) -> OnboardingAgentResponse:
        ...

    async def handle_messages(
        self,
        business_user_id: UUID,
        messages: list[ConversationMessage],
    ) -> str | None:
        raise NotImplementedError
