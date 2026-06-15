from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID
from langchain_gigachat import GigaChat

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from agent.api.schemas import ConversationMessage
from agent.application.dto.agent_context import AgentPlannerContextDto
from agent.application.ports.course_context import CourseContextPort
from agent.application.ports.analytics_context import AnalyticsContextPort
from agent.application.ports.schedule_context import ScheduleContextPort
from agent.conversation_agent.runtime_context import AgentExecutionContext
from agent.conversation_agent.tools.planner_tools import build_planner_tools


@dataclass(frozen=True, slots=True)
class MainAssistantAgentResult:
    assistant_text: str


async def run_main_assistant_agent(
    *,
    llm: GigaChat,
    business_user_id: UUID,
    messages: list[ConversationMessage],
    planner_context: AgentPlannerContextDto,
    course_context: CourseContextPort,
    schedule_context: ScheduleContextPort,
    analytics_context: AnalyticsContextPort,
    callbacks: list[Any] | None = None,
) -> MainAssistantAgentResult:
    execution_context = AgentExecutionContext(
        business_user_id=business_user_id,
    )

    tools = build_planner_tools(
        execution_context=execution_context,
        planner_context=planner_context,
        course_context=course_context,
        schedule_context=schedule_context,
        analytics_context=analytics_context,
    )

    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=_build_system_prompt(planner_context),
    )

    config: RunnableConfig | None = None

    if callbacks:
        config = RunnableConfig(callbacks=callbacks)

    result = await agent.ainvoke(
        {"messages": _to_langchain_messages(messages)},  # type: ignore[arg-type]
        config=config,
    )

    return MainAssistantAgentResult(
        assistant_text=_extract_last_ai_text(result),
    )


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
            # Не доверяем system-сообщениям из Gateway/session history как настоящему system prompt.
            result.append(HumanMessage(content=f"[session system note] {message.content}"))

    return result


def _build_system_prompt(context: AgentPlannerContextDto) -> str:
    courses = "\n".join(
        f"- id={course.id}; title={course.title}; description={course.description or ''}"
        for course in context.courses
    ) or "- курсов пока нет"

    print(courses)
    observations = "\n".join(
        f"- {observation.description}"
        for observation in context.analytics_observations
    ) or "- наблюдений пока нет"

    reminders = "\n".join(
        f"- id={reminder.id}; title={reminder.title}; remind_at={reminder.remind_at}; description={reminder.description or ''}"
        for reminder in context.reminders
    ) or "- напоминаний пока нет"

    deadlines = "\n".join(
        f"- id={deadline.id}; title={deadline.title}; due_at={deadline.due_at}; description={deadline.description or ''}"
        for deadline in context.deadlines
    ) or "- дедлайнов пока нет"

    date_observations = "\n".join(
        f"- id={observation.id}; starts_on={observation.starts_on}; ends_on={observation.ends_on}; description={observation.description}"
        for observation in context.date_observations
    ) or "- наблюдений на ближайшие даты пока нет"

    return f"""
Ты Planner assistant.

Ты работаешь только с текущим пользователем.
Никогда не проси у пользователя user_id.
Не используй UUID, которые написал пользователь.
Можно использовать только UUID, которые уже есть в этом системном контексте.

Если пользователь хочет создать новый курс, вызови tool create_course.
Не говори, что курс создан, пока create_course не был успешно вызван.

Отвечай на русском, если пользователь пишет на русском.

Текущий день: {context.today}

Профиль пользователя:
- login: {context.user_profile.login}
- name: {context.user_profile.name}
- language: {context.user_profile.language}
- region: {context.user_profile.region}
- utc_offset_minutes: {context.user_profile.utc_offset_minutes}

Курсы пользователя:
{courses}

Память о пользователе:
{observations}

Напоминания:
{reminders}

Дедлайны:
{deadlines}

Наблюдения на ближайшие даты:
{date_observations}
""".strip()


def _extract_last_ai_text(result: Any) -> str:
    messages = result.get("messages", []) if isinstance(result, dict) else []

    for message in reversed(messages):
        if isinstance(message, AIMessage):
            return _message_text(message)

        if getattr(message, "type", None) == "ai":
            return _message_text(message)

    return ""


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