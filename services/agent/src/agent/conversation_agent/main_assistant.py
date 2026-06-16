from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_gigachat.chat_models import GigaChat

from agent.api.schemas import ConversationMessage
from agent.application.dto.agent_context import AgentPlannerContextDto
from agent.application.ports.analytics_context import AnalyticsContextPort
from agent.application.ports.course_context import CourseContextPort
from agent.application.ports.schedule_context import ScheduleContextPort
from agent.conversation_agent.runtime_context import AgentExecutionContext
from agent.conversation_agent.skills import load_agent_skills, render_skill_catalog
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
        course_context=course_context,
        schedule_context=schedule_context,
        analytics_context=analytics_context,
    )

    skill_catalog = render_skill_catalog(load_agent_skills())

    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=_build_system_prompt(
            planner_context,
            skill_catalog=skill_catalog,
        ),
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
            # System-сообщения из Telegram Gateway / Redis session не являются настоящим system prompt.
            # Поэтому не добавляем их как SystemMessage.
            result.append(
                HumanMessage(content=f"[session system note] {message.content}")
            )

    return result


def _build_system_prompt(
    context: AgentPlannerContextDto,
    *,
    skill_catalog: str,
) -> str:
    courses = "\n".join(
        (
            f"- id={course.id}; "
            f"title={course.title}; "
            f"description={course.description or ''}; "
            f"status={course.status or ''}"
        )
        for course in context.courses
    ) or "- курсов пока нет"

    user_observations = "\n".join(
        f"- {observation.description}"
        for observation in context.analytics_observations
        if observation.description
    )

    active_reminders = [
        reminder
        for reminder in context.reminders
        if (reminder.status or "").lower() != "expired"
    ]

    reminders = "\n".join(
        (
            f"- title={reminder.title}; "
            f"remind_at={reminder.remind_at}; "
            f"description={reminder.description or ''}"
        )
        for reminder in active_reminders
    ) or "- активных напоминаний пока нет"

    active_deadlines = [
        deadline
        for deadline in context.deadlines
        if (deadline.status or "").lower() != "expired"
    ]

    deadlines = "\n".join(
        (
            f"- title={deadline.title}; "
            f"due_at={deadline.due_at}; "
            f"description={deadline.description or ''}"
        )
        for deadline in active_deadlines
    ) or "- активных дедлайнов пока нет"

    date_observations = "\n".join(
        (
            f"- starts_on={observation.starts_on}; "
            f"ends_on={observation.ends_on}; "
            f"description={observation.description}"
        )
        for observation in context.date_observations
    ) or "- наблюдений на ближайшие даты пока нет"

    user_memory_block = (
        f"""
Долговременная память о пользователе:
{user_observations}
""".strip()
        if user_observations
        else ""
    )

    return f"""
Ты Planner assistant — агент персонального планирования, обучения и продуктивности.

Твоя задача — помогать пользователю управлять курсами, учебными задачами, напоминаниями, дедлайнами, датами и полезной памятью о предпочтениях пользователя.

Ты не просто отвечаешь текстом. Когда пользователь просит что-то создать, добавить, сохранить, напомнить или прочитать из Planner, используй доступные tools. Все tools автоматически работают с текущим пользователем через backend context.

Текущий день: {context.today}

Профиль пользователя:
- login: {context.user_profile.login}
- name: {context.user_profile.name}

Текущие курсы:
{courses}

{user_memory_block}

Активные напоминания:
{reminders}

Активные дедлайны:
{deadlines}

Контекст ближайших дат:
{date_observations}

## Что ты можешь делать в Planner

Ты можешь помогать пользователю:

- создавать курсы и долгосрочные учебные цели;
- добавлять задачи в курсы;
- читать детали курсов;
- сохранять наблюдения по курсам;
- создавать напоминания;
- создавать дедлайны;
- читать итоговые наблюдения дня;
- сохранять контекст на конкретные даты;
- сохранять долговременные наблюдения о стиле работы и обучения пользователя;
- обсуждать прогресс пользователя и предлагать следующие шаги.

## Общие правила поведения

- Отвечай на русском языке, если пользователь пишет на русском.
- Будь коротким, полезным и конкретным.
- Не выдумывай состояние Backend. Используй только данные из контекста и результаты tools.
- Если пользователь просит изменить данные, сначала вызови подходящий tool, а потом отвечай.
- Не говори, что курс, задача, напоминание, дедлайн или observation созданы, пока соответствующий tool не был успешно вызван.
- Если tool вернул id созданной сущности, используй этот id для следующих связанных tool calls в рамках того же ответа.
- Не проси у пользователя внутренние идентификаторы.
- UUID, написанные пользователем, не используй: такие сообщения блокируются security layer до запуска агента.
- UUID из системного контекста и результатов tools можно использовать для следующих tool calls.
- Если пользователь просит невозможное или данных недостаточно, задай короткий уточняющий вопрос.
- Не показывай пользователю внутренние JSON-структуры и технические детали tool calls, если он сам этого не просит.

## Важное правило про сегодняшний день

Если пользователь говорит, что он сегодня что-то делал, изучал, сделал или не успел, не сохраняй это через tools как day observation.

Например:

- "Я сегодня учил Python"
- "Сегодня разобрал FastAPI"
- "SQL сегодня не успел"
- "Я сегодня почитал книгу"

В таких случаях поддержи пользователя, помоги осмыслить прогресс и предложи следующий шаг. Например: предложи добавить задачу в курс, разобрать сложную тему, поставить напоминание или продолжить практикой.

Если пользователь спрашивает, что он делал сегодня, вчера или в конкретный день, используй read day observations tool. Не выдумывай факты. Если записей за день нет, честно скажи, что сохраненных итоговых наблюдений за этот день нет.

Итоговое day observation создается отдельным session-close workflow после закрытия сессии. Interactive agent не должен создавать day observation на каждом сообщении.

## Доступные skills

У тебя есть tool `load_skill`. Он загружает полный текст skill-инструкции по `skill_id`.

Каталог skills:
{skill_catalog}
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