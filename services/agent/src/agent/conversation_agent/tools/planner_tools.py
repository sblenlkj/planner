from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from agent.application.ports.analytics_context import AnalyticsContextPort
from agent.application.ports.course_context import CourseContextPort
from agent.application.ports.schedule_context import ScheduleContextPort
from agent.conversation_agent.runtime_context import AgentExecutionContext

from agent.conversation_agent.skills import get_agent_skill

class LoadSkillArgs(BaseModel):
    skill_id: str = Field(
        description=(
            "Идентификатор skill из skill catalog. "
            "Например: course_planning или user_memory."
        )
    )

class CreateCourseArgs(BaseModel):
    title: str = Field(description="Название курса, который нужно создать.")
    description: str | None = Field(
        default=None,
        description="Краткое описание цели курса.",
    )


class CreateCourseTaskArgs(BaseModel):
    course_id: str = Field(
        description=(
            "UUID курса. Используй только UUID из системного контекста или из результата create_course. "
            "Не используй UUID, написанный пользователем."
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
            "Если пользователь указал относительное время, преобразуй его относительно текущей даты из системного контекста."
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
            "Если пользователь указал относительное время, преобразуй его относительно текущей даты из системного контекста."
        )
    )
    title: str = Field(description="Короткий заголовок дедлайна.")
    description: str | None = Field(
        default=None,
        description="Дополнительное описание дедлайна.",
    )
    course_id: str | None = Field(
        default=None,
        description=(
            "UUID курса, если дедлайн связан с курсом. "
            "Используй только UUID из системного контекста или результата tool call."
        ),
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
    course_id: str = Field(
        description=(
            "UUID курса. Используй только UUID из системного контекста или из результата create_course."
        )
    )
    title: str = Field(description="Короткий заголовок наблюдения по курсу.")
    description: str = Field(description="Содержательное наблюдение по курсу.")


class ReadCourseDetailsArgs(BaseModel):
    course_id: str = Field(
        description=(
            "UUID курса. Используй только UUID из системного контекста или из результата create_course."
        )
    )
    with_observations: bool = Field(
        default=True,
        description="Нужно ли читать наблюдения курса.",
    )
    with_tasks: bool = Field(
        default=True,
        description="Нужно ли читать задачи курса.",
    )

class ReadDayObservationsArgs(BaseModel):
    day: str = Field(
        description=(
            "День, за который нужно прочитать итоговые day observations, "
            "в формате YYYY-MM-DD. Если пользователь спрашивает про сегодня, "
            "используй текущий день из system context."
        ),
    )

async def load_skill(skill_id: str) -> str:
    skill = get_agent_skill(skill_id)

    return (
        f"# {skill.title}\n\n"
        f"Описание: {skill.description}\n\n"
        f"{skill.body}"
    )

def build_planner_tools(
    *,
    execution_context: AgentExecutionContext,
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
        course_id: str,
        title: str,
        description: str | None = None,
        priority: int = 2,
    ) -> str:
        parsed_course_id = _parse_uuid(course_id, field_name="course_id")

        task = await course_context.create_course_task(
            parsed_course_id,
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
        course_id: str | None = None,
    ) -> str:
        deadline_datetime = _parse_datetime(due_at)

        parsed_course_id: UUID | None = None
        if course_id:
            parsed_course_id = _parse_uuid(course_id, field_name="course_id")

        deadline = await schedule_context.create_deadline(
            execution_context.business_user_id,
            due_at=deadline_datetime,
            title=title,
            description=description,
            course_id=parsed_course_id,
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
    
    async def read_day_observations(
        day: str,
    ) -> str:
        target_date = _parse_date(day)

        observations = await schedule_context.list_schedule_day_observations(
            execution_context.business_user_id,
            date_=target_date,
        )

        if not observations:
            return (
                "За этот день day observations не найдены.\n"
                f"day: {target_date.isoformat()}\n"
                "Я не знаю, что пользователь делал в этот день."
            )

        items = "\n".join(
            f"- id={observation.id}; description={observation.description}"
            for observation in observations
        )

        return (
            "Day observations найдены.\n"
            f"day: {target_date.isoformat()}\n"
            f"{items}"
        )

    async def read_course_details(
        course_id: str,
        with_observations: bool = True,
        with_tasks: bool = True,
    ) -> str:
        parsed_course_id = _parse_uuid(course_id, field_name="course_id")

        detailed_course = await course_context.get_course(
            parsed_course_id,
            with_tasks=with_tasks,
            with_observations=with_observations,
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
                "course_id должен быть UUID из системного контекста или из результата create_course."
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
            coroutine=load_skill,
            name="load_skill",
            description=(
                "Загружает полный текст skill-инструкции по skill_id из skill catalog. "
                "Используй перед сложными действиями, если нужно уточнить правила работы с курсами, памятью или другими сценариями."
            ),
            args_schema=LoadSkillArgs,
        ),
        StructuredTool.from_function(
            coroutine=read_day_observations,
            name="read_day_observations",
            description=(
                "Читает итоговые day observations пользователя за конкретную дату. "
                "Используй, когда пользователь спрашивает, что он делал сегодня, вчера "
                "или в конкретный день. Этот tool ничего не создает."
            ),
            args_schema=ReadDayObservationsArgs,
        ),
    ]


def _parse_uuid(value: str, *, field_name: str) -> UUID:
    try:
        return UUID(value.strip())
    except ValueError as exc:
        raise ValueError(f"{field_name} должен быть UUID. Получено: {value!r}") from exc


def _parse_date(value: str) -> date:
    return date.fromisoformat(value.strip())


def _parse_datetime(value: str) -> datetime:
    normalized = value.strip()

    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"

    return datetime.fromisoformat(normalized)


def _format_course_details(course) -> str:
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