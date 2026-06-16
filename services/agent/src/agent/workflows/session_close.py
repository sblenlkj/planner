from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, TypedDict
from uuid import UUID

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_gigachat.chat_models import GigaChat
from langgraph.graph import END, START, StateGraph

from agent.api.schemas import ConversationMessage
from agent.application.ports.schedule_context import ScheduleContextPort


class SessionCloseGraphState(TypedDict):
    today: date
    input_messages: list[ConversationMessage]

    llm_messages: list[BaseMessage]
    observation_text: str | None

    observation_created: bool
    observation_id: UUID | None
    observation_description: str | None


@dataclass(frozen=True, slots=True)
class SessionCloseWorkflowResult:
    observation_created: bool
    description: str | None = None
    observation_id: UUID | None = None


def build_session_close_graph(
    *,
    llm: GigaChat,
    business_user_id: UUID,
    schedule_context: ScheduleContextPort,
):
    async def build_context_node(
        state: SessionCloseGraphState,
    ) -> SessionCloseGraphState:
        return {
            **state,
            "llm_messages": [
                SystemMessage(content=_system_prompt(state["today"])),
                *_to_langchain_messages(state["input_messages"]),
            ],
        }

    async def call_llm_node(
        state: SessionCloseGraphState,
    ) -> SessionCloseGraphState:
        response = await llm.ainvoke(state["llm_messages"])
        observation_text = _normalize_observation_text(_message_text(response))

        return {
            **state,
            "observation_text": observation_text,
        }

    async def save_day_observation_node(
        state: SessionCloseGraphState,
    ) -> SessionCloseGraphState:
        description = state["observation_text"]

        if description is None:
            return {
                **state,
                "observation_created": False,
                "observation_id": None,
                "observation_description": None,
            }

        observation = await schedule_context.create_schedule_day_observation(
            business_user_id,
            date_=state["today"],
            description=description,
        )

        return {
            **state,
            "observation_created": True,
            "observation_id": observation.id,
            "observation_description": observation.description,
        }

    graph_builder = StateGraph(SessionCloseGraphState)

    graph_builder.add_node("build_context", build_context_node)
    graph_builder.add_node("call_llm", call_llm_node)
    graph_builder.add_node("save_day_observation", save_day_observation_node)

    graph_builder.add_edge(START, "build_context")
    graph_builder.add_edge("build_context", "call_llm")
    graph_builder.add_edge("call_llm", "save_day_observation")
    graph_builder.add_edge("save_day_observation", END)

    return graph_builder.compile()


async def run_session_close_workflow(
    *,
    llm: GigaChat,
    business_user_id: UUID,
    messages: list[ConversationMessage],
    schedule_context: ScheduleContextPort,
    today: date | None = None,
    config: RunnableConfig | None = None,
) -> SessionCloseWorkflowResult:
    resolved_today = today or date.today()

    graph = build_session_close_graph(
        llm=llm,
        business_user_id=business_user_id,
        schedule_context=schedule_context,
    )

    final_state = await graph.ainvoke(
        {
            "today": resolved_today,
            "input_messages": messages,
            "llm_messages": [],
            "observation_text": None,
            "observation_created": False,
            "observation_id": None,
            "observation_description": None,
        },  # type: ignore[arg-type]
        config=config,
    )

    return SessionCloseWorkflowResult(
        observation_created=bool(final_state.get("observation_created", False)),
        description=final_state.get("observation_description"),
        observation_id=final_state.get("observation_id"),
    )


def _system_prompt(today: date) -> str:
    return f"""
Ты Session Close Workflow системы Planner.

Текущая дата: {today.isoformat()}

Прочитай transcript закрытой сессии пользователя.

Верни ОДНУ строку:
- либо короткое наблюдение о том, что пользователь реально сделал, изучал, выполнил, не выполнил или сообщил о своем состоянии;
- либо строго nan, если полезного факта нет.

Сохраняй только факты о пользователе.
Не сохраняй вопросы.
Не сохраняй ответы ассистента.
Не сохраняй предложения ассистента.
Не сохраняй неподтвержденные планы.
Не сохраняй обычный small talk.
Не сохраняй фразы без результата.

Формат ответа:
- обычный текст без JSON;
- без markdown;
- без заголовков;
- если факта нет — только nan.

Примеры:

Transcript:
user: Привет
assistant: Привет! Чем могу помочь?
Ответ:
nan

Transcript:
user: Напомни мне завтра позвонить маме
assistant: Готово, напомню завтра.
Ответ:
nan

Transcript:
user: Сегодня я прочитал 20 страниц книги по Python
assistant: Отлично, я запомню.
Ответ:
Пользователь сегодня прочитал 20 страниц книги по Python.

Transcript:
user: Я хотел заняться английским, но не успел
assistant: Понял.
Ответ:
Пользователь хотел заняться английским, но не успел.

Transcript:
user: Принесло ли это результаты?
assistant: Да, это может помочь.
Ответ:
nan

Transcript:
assistant: Может быть, сегодня продолжить курс по Python?
user: Да, я сегодня решил две задачи по async.
Ответ:
Пользователь сегодня решил две задачи по async.

Теперь обработай transcript.
""".strip()


def _to_langchain_messages(
    messages: list[ConversationMessage],
) -> list[BaseMessage]:
    result: list[BaseMessage] = []

    for message in messages:
        if message.role == "user":
            result.append(HumanMessage(content=message.content))
        elif message.role == "assistant":
            result.append(AIMessage(content=message.content))
        elif message.role == "system":
            result.append(
                HumanMessage(content=f"[session system note] {message.content}")
            )

    return result


def _normalize_observation_text(value: str) -> str | None:
    text = value.strip()

    if not text:
        return None

    if "nan" in text.lower():
        return None

    return text


def _message_text(message: Any) -> str:
    content = getattr(message, "content", "")

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts: list[str] = []

        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text") or item.get("content")
                if text:
                    parts.append(str(text))

        return "\n".join(parts).strip()

    return str(content)