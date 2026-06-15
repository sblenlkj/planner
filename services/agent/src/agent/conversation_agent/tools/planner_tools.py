from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from agent.application.dto.agent_context import AgentPlannerContextDto
from agent.application.dto.course import CourseDto
from agent.application.ports.analytics_context import AnalyticsContextPort
from agent.application.ports.course_context import CourseContextPort
from agent.application.ports.schedule_context import ScheduleContextPort
from agent.conversation_agent.runtime_context import AgentExecutionContext


class CreateCourseArgs(BaseModel):
    title: str = Field(description="Название курса, который нужно создать.")
    description: str | None = Field(
        default=None,
        description="Краткое описание цели курса.",
    )


class CreateCourseTaskArgs(BaseModel):
    course_ref: str = Field(
        description=(
            "Название или id курса из текущего системного контекста. "
            "Не используй id, который написал пользователь руками."
        )
    )
    title: str = Field(description="Название задачи курса.")
    description: str | None = Field(
        default=None,
        description="Краткое описание задачи.",
    )
    priority: int = Field(
        default=2,
        description="Приоритет задачи: 1 — высокий, 2 — обычный, 3 — низкий.",
    )


class CreateReminderArgs(BaseModel):
    remind_at: str = Field(
        description=(
            "Дата и время напоминания в ISO формате. "
            "Если пользователь указал относительное время, преобразуй его относительно текущей даты из контекста."
        )
    )
    title: str = Field(description="Короткий заголовок напоминания.")
    description: str | None = Field(
        default=None,
        description="Дополнительное описание напоминания.",
    )


class CreateDeadlineArgs(BaseModel):
    due_at: str = Field(
        description=(
            "Дата и время дедлайна в ISO формате. "
            "Если пользователь указал относительное время, преобразуй его относительно текущей даты из контекста."
        )
    )
    title: str = Field(description="Короткий заголовок дедлайна.")
    description: str | None = Field(
        default=None,
        description="Дополнительное описание дедлайна.",
    )
    course_ref: str | None = Field(
        default=None,
        description="Название или id курса из текущего контекста, если дедлайн связан с курсом.",
    )


class RememberUserObservationArgs(BaseModel):
    description: str = Field(
        description=(
            "Короткое устойчивое наблюдение о пользователе: предпочтение, привычка, стиль работы, "
            "важная особенность планирования."
        )
    )
    scope: str = Field(
        default="productivity",
        description=(
            "Область наблюдения. Разрешенные значения обычно: education, productivity, communication, food, sport."
        ),
    )


class CreateDateObservationArgs(BaseModel):
    starts_on: str = Field(description="Дата начала в формате YYYY-MM-DD.")
    ends_on: str | None = Field(
        default=None,
        description="Дата окончания в формате YYYY-MM-DD. Если период один день, можно не указывать.",
    )
    description: str = Field(
        description="Ограничение, событие или важный контекст на дату/период.",
    )


class CreateCourseObservationArgs(BaseModel):
    course_ref: str = Field(
        description="Название или id курса из текущего системного контекста."
    )
    title: str = Field(description="Короткий заголовок наблюдения по курсу.")
    description: str = Field(description="Содержательное наблюдение по курсу.")


class ReadCourseDetailsArgs(BaseModel):
    course_ref: str = Field(
        description="Название или id курса из текущего системного контекста."
    )


def build_planner_tools(
    *,
    execution_context: AgentExecutionContext,
    planner_context: AgentPlannerContextDto,
    course_context: CourseContextPort,
    schedule_context: ScheduleContextPort,
    analytics_context: AnalyticsContextPort,
) -> list[StructuredTool]:
    async def create_course(
        title: str,
        description: str | None = None,
    ) -> str:
        course = await course_context.create_course(
            execution_context.business_user_id,
            title=title,
            description=description,
        )

        return (
            "Курс создан.\n"
            f"id: {course.id}\n"
            f"title: {course.title}\n"
            f"description: {course.description or ''}"
        )

    async def create_course_task(
        course_ref: str,
        title: str,
        description: str | None = None,
        priority: int = 2,
    ) -> str:
        course = _resolve_course(planner_context, course_ref)

        task = await course_context.create_course_task(
            course.id,
            title=title,
            description=description,
            priority=priority,
        )

        return (
            "Задача курса создана.\n"
            f"id: {task.id}\n"
            f"course_id: {task.course_id}\n"
            f"title: {task.title}\n"
            f"description: {task.description or ''}\n"
            f"priority: {task.priority}"
        )

    async def create_reminder(
        remind_at: str,
        title: str,
        description: str | None = None,
    ) -> str:
        reminder_datetime = _parse_datetime(remind_at)

        reminder = await schedule_context.create_reminder(
            execution_context.business_user_id,
            remind_at=reminder_datetime,
            title=title,
            description=description,
        )

        return (
            "Напоминание создано.\n"
            f"id: {reminder.id}\n"
            f"title: {reminder.title}\n"
            f"remind_at: {reminder.remind_at.isoformat()}\n"
            f"description: {reminder.description or ''}"
        )

    async def create_deadline(
        due_at: str,
        title: str,
        description: str | None = None,
        course_ref: str | None = None,
    ) -> str:
        deadline_datetime = _parse_datetime(due_at)

        course_id: UUID | None = None
        if course_ref:
            course_id = _resolve_course(planner_context, course_ref).id

        deadline = await schedule_context.create_deadline(
            execution_context.business_user_id,
            due_at=deadline_datetime,
            title=title,
            description=description,
            course_id=course_id,
            course_task_id=None,
        )

        return (
            "Дедлайн создан.\n"
            f"id: {deadline.id}\n"
            f"title: {deadline.title}\n"
            f"due_at: {deadline.due_at.isoformat()}\n"
            f"description: {deadline.description or ''}"
        )

    async def remember_user_observation(
        description: str,
        scope: str = "productivity",
    ) -> str:
        observation = await analytics_context.create_observation(
            execution_context.business_user_id,
            description=description,
            scope=scope,
        )

        return (
            "Наблюдение о пользователе сохранено.\n"
            f"id: {observation.id}\n"
            f"description: {observation.description}"
        )

    async def create_date_observation(
        starts_on: str,
        description: str,
        ends_on: str | None = None,
    ) -> str:
        start_date = _parse_date(starts_on)
        end_date = _parse_date(ends_on) if ends_on else start_date

        observation = await schedule_context.create_schedule_date_observation(
            execution_context.business_user_id,
            starts_on=start_date,
            ends_on=end_date,
            description=description,
        )

        return (
            "Наблюдение на дату сохранено.\n"
            f"id: {observation.id}\n"
            f"starts_on: {observation.starts_on.isoformat()}\n"
            f"ends_on: {observation.ends_on.isoformat() if observation.ends_on else ''}\n"
            f"description: {observation.description}"
        )

    async def create_course_observation(
        course_ref: str,
        title: str,
        description: str,
    ) -> str:
        course = _resolve_course(planner_context, course_ref)

        observation = await course_context.create_course_observation(
            course.id,
            title=title,
            description=description,
        )

        return (
            "Наблюдение по курсу сохранено.\n"
            f"id: {observation.id}\n"
            f"course_id: {observation.course_id}\n"
            f"title: {observation.title or ''}\n"
            f"description: {observation.description}"
        )

    async def read_course_details(course_ref: str) -> str:
        course = _resolve_course(planner_context, course_ref)

        detailed_course = await course_context.get_course(
            course.id,
            with_tasks=True,
            with_observations=True,
        )

        return _format_course_details(detailed_course)

    return [
        StructuredTool.from_function(
            coroutine=create_course,
            name="create_course",
            description=(
                "Создает новый курс для текущего пользователя. "
                "Используй, когда пользователь хочет начать изучать новую тему, "
                "добавить учебный трек или создать долгосрочную учебную цель."
            ),
            args_schema=CreateCourseArgs,
        ),
        StructuredTool.from_function(
            coroutine=create_course_task,
            name="create_course_task",
            description=(
                "Создает задачу внутри существующего курса. "
                "Курс выбирай только из текущего системного контекста."
            ),
            args_schema=CreateCourseTaskArgs,
        ),
        StructuredTool.from_function(
            coroutine=create_reminder,
            name="create_reminder",
            description=(
                "Создает напоминание для текущего пользователя. "
                "Используй, когда пользователь просит напомнить о действии в конкретное время."
            ),
            args_schema=CreateReminderArgs,
        ),
        StructuredTool.from_function(
            coroutine=create_deadline,
            name="create_deadline",
            description=(
                "Создает дедлайн для текущего пользователя. "
                "Используй, когда есть срок выполнения задачи или учебной цели."
            ),
            args_schema=CreateDeadlineArgs,
        ),
        StructuredTool.from_function(
            coroutine=remember_user_observation,
            name="remember_user_observation",
            description=(
                "Сохраняет устойчивое наблюдение о пользователе в analytics context. "
                "Используй для предпочтений, привычек, стиля планирования и долговременных особенностей."
            ),
            args_schema=RememberUserObservationArgs,
        ),
        StructuredTool.from_function(
            coroutine=create_date_observation,
            name="create_date_observation",
            description=(
                "Сохраняет наблюдение или ограничение на конкретную дату или период. "
                "Используй для событий, занятости, ограничений и контекста ближайших дней."
            ),
            args_schema=CreateDateObservationArgs,
        ),
        StructuredTool.from_function(
            coroutine=create_course_observation,
            name="create_course_observation",
            description=(
                "Сохраняет наблюдение по конкретному курсу. "
                "Используй для прогресса, сложности, заметок и важных фактов о курсе."
            ),
            args_schema=CreateCourseObservationArgs,
        ),
        StructuredTool.from_function(
            coroutine=read_course_details,
            name="read_course_details",
            description=(
                "Читает подробности конкретного курса: задачи и наблюдения. "
                "Используй, когда пользователь спрашивает состояние или детали курса."
            ),
            args_schema=ReadCourseDetailsArgs,
        ),
    ]


def _resolve_course(
    planner_context: AgentPlannerContextDto,
    course_ref: str,
) -> CourseDto:
    normalized_ref = course_ref.strip().lower()

    for course in planner_context.courses:
        if str(course.id) == course_ref.strip():
            return course

    exact_title_matches = [
        course
        for course in planner_context.courses
        if course.title.strip().lower() == normalized_ref
    ]
    if len(exact_title_matches) == 1:
        return exact_title_matches[0]

    partial_title_matches = [
        course
        for course in planner_context.courses
        if normalized_ref in course.title.strip().lower()
        or course.title.strip().lower() in normalized_ref
    ]
    if len(partial_title_matches) == 1:
        return partial_title_matches[0]

    available_courses = "\n".join(
        f"- id={course.id}; title={course.title}"
        for course in planner_context.courses
    ) or "- курсов в текущем контексте нет"

    raise ValueError(
        "Не удалось однозначно выбрать курс из текущего контекста.\n"
        f"Переданный course_ref: {course_ref}\n"
        f"Доступные курсы:\n{available_courses}"
    )


def _parse_date(value: str) -> date:
    return date.fromisoformat(value.strip())


def _parse_datetime(value: str) -> datetime:
    normalized = value.strip()

    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"

    parsed = datetime.fromisoformat(normalized)

    return parsed


def _format_course_details(course: CourseDto) -> str:
    tasks = "\n".join(
        (
            f"- id={task.id}; title={task.title}; "
            f"status={task.status}; priority={task.priority}; "
            f"progress={task.progress}; description={task.description or ''}"
        )
        for task in course.tasks
    ) or "- задач пока нет"

    observations = "\n".join(
        (
            f"- id={observation.id}; title={observation.title or ''}; "
            f"description={observation.description}"
        )
        for observation in course.observations
    ) or "- наблюдений пока нет"

    return (
        "Детали курса.\n"
        f"id: {course.id}\n"
        f"title: {course.title}\n"
        f"description: {course.description or ''}\n"
        f"status: {course.status or ''}\n\n"
        f"Задачи:\n{tasks}\n\n"
        f"Наблюдения:\n{observations}"
    )