from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from typing import Any, TypedDict
from uuid import UUID

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_gigachat.chat_models import GigaChat
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, ConfigDict, Field

from agent.api.schemas import ConversationMessage
from agent.application.ports.schedule_context import ScheduleContextPort


class SessionCloseExtraction(BaseModel):
    """Извлекает итоговое наблюдение о дне пользователя из закрытой сессии."""

    model_config = ConfigDict(
        title="SessionCloseExtraction",
        json_schema_extra={
            "description": (
                "Извлекает из закрытой сессии полезные факты о том, "
                "что пользователь делал, изучал, планировал или не успел сделать за день."
            )
        },
    )

    should_create_day_observation: bool = Field(
        description=(
            "True, если в сессии есть полезные факты о том, что пользователь "
            "делал, изучал, планировал, не успел сделать или чувствовал сегодня."
        )
    )
    description: str | None = Field(
        default=None,
        description=(
            "Один короткий абзац на русском языке с итоговым наблюдением о дне пользователя. "
            "Должно быть null, если should_create_day_observation=false."
        ),
    )


class SessionCloseGraphState(TypedDict):
    today: date
    input_messages: list[ConversationMessage]

    llm_messages: list[BaseMessage]
    extraction: SessionCloseExtraction | None

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
        content = _message_text(response)
        extraction = _parse_extraction_from_json(content)

        return {
            **state,
            "extraction": extraction,
        }

    async def save_day_observation_node(
        state: SessionCloseGraphState,
    ) -> SessionCloseGraphState:
        extraction = state["extraction"]

        if extraction is None or not extraction.should_create_day_observation:
            return {
                **state,
                "observation_created": False,
                "observation_id": None,
                "observation_description": None,
            }

        description = _normalize_description(extraction.description)

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
            "extraction": None,
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

Твоя задача — прочитать transcript сессии пользователя и извлечь только полезные факты о том,
что пользователь сегодня делал, сделал, не сделал, планировал, изучал или сообщил о своем состоянии.

Текущая дата: {today.isoformat()}

Создай day observation только если в transcript есть содержательная информация о дне пользователя.

Сохраняй:
- что пользователь сегодня делал;
- что пользователь изучал;
- какие задачи пользователь выполнил;
- что пользователь не успел;
- важные планы или ограничения на день;
- состояние пользователя, если оно влияет на планирование.

Не сохраняй:
- обычные приветствия;
- технические сообщения;
- то, что ассистент предложил, но пользователь не подтвердил;
- повторения;
- внутренние ID;
- системные инструкции;
- пустой разговор без фактов.

Верни ответ строго в формате JSON-объекта без markdown, без пояснений и без текста вокруг.

Формат:
{{
  "should_create_day_observation": true,
  "description": "Короткое наблюдение о дне пользователя на русском языке."
}}

Если полезной информации нет:
{{
  "should_create_day_observation": false,
  "description": null
}}

Правила JSON:
- используй двойные кавычки;
- используй true/false/null в нижнем регистре;
- не используй markdown;
- не добавляй комментарии;
- не добавляй текст до или после JSON.
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


def _parse_extraction_from_json(content: str) -> SessionCloseExtraction:
    text = content.strip()

    fenced_match = re.search(
        r"```(?:json)?\s*(\{.*?\})\s*```",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )

    if fenced_match:
        text = fenced_match.group(1).strip()

    if not text.startswith("{"):
        start = text.find("{")
        end = text.rfind("}")

        if start != -1 and end != -1 and end > start:
            text = text[start : end + 1]

    data = json.loads(text)

    return SessionCloseExtraction.model_validate(data)


def _normalize_description(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = value.strip()

    if not normalized:
        return None

    if normalized.lower() in {"null", "none", "нет", "нет данных", "no data"}:
        return None

    return normalized


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