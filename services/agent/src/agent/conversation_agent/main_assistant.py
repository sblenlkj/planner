from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from agent.api.schemas import ChatMessage


@dataclass(frozen=True, slots=True)
class MainAssistantAgentResult:
    assistant_text: str


async def run_main_assistant_agent(
    *,
    llm: Any,
    business_user_id: UUID,
    messages: list[ChatMessage],
    langfuse_config: dict[str, Any] | None = None,
) -> MainAssistantAgentResult:
    langchain_messages = [
        (
            "system",
            (
                "Ты основной Planner assistant. "
                "Пользователь уже прошёл onboarding. "
                "Помогай обсуждать день, reminders, deadlines, courses и tasks. "
                "Пока backend tools не подключены, не утверждай, что ты реально изменил данные. "
                "Если нужно действие в backend, скажи, что это будет следующий шаг реализации."
            ),
        ),
        *[(message.role, message.content) for message in messages],
    ]

    response = await llm.ainvoke(
        langchain_messages,
        config=langfuse_config,
    )

    return MainAssistantAgentResult(
        assistant_text=response.content,
    )