from __future__ import annotations

from uuid import UUID

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from agent.application.ports.course_context import CourseContextPort
from agent.conversation_agent.runtime_context import AgentExecutionContext


class CreateCourseArgs(BaseModel):
    title: str = Field(description="Название курса, который нужно создать.")
    description: str | None = Field(
        default=None,
        description="Краткое описание цели курса.",
    )


def build_planner_tools(
    *,
    execution_context: AgentExecutionContext,
    course_context: CourseContextPort,
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

    return [
        StructuredTool.from_function(
            coroutine=create_course,
            name="create_course",
            description=(
                "Создает новый курс для текущего пользователя. "
                "Используй этот инструмент, когда пользователь хочет начать изучать тему, "
                "добавить новый учебный трек или создать долгосрочную цель."
            ),
            args_schema=CreateCourseArgs,
        )
    ]