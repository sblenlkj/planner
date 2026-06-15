from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from agent.api.schemas import ChatMessage


@dataclass(frozen=True, slots=True)
class OnboardingAgentResult:
    assistant_text: str
    user_is_ready: bool


async def run_onboarding_agent(
    *,
    llm: Any,
    business_user_id: UUID,
    messages: list[ChatMessage],
    langfuse_config: dict[str, Any] | None = None,
) -> OnboardingAgentResult:
    langchain_messages = [
        (
            "system",
            (
                "Ты onboarding agent для Planner. "
                "Твоя задача — кратко объяснить пользователю, зачем нужен planner, "
                "и собрать базовые данные: часовой пояс, обычный режим сна, работы, "
                "свободное время, цели, reminders и deadlines. "
                "Пока не отмечай пользователя готовым автоматически. "
                "Отвечай кратко и задай один следующий вопрос."
            ),
        ),
        *[(message.role, message.content) for message in messages],
    ]

    response = await llm.ainvoke(
        langchain_messages,
        config=langfuse_config,
    )

    return OnboardingAgentResult(
        assistant_text=response.content,
        user_is_ready=False,
    )