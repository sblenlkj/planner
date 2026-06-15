from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from backend.context.course.application.dto.course_read_models import (
    CourseDetails,
    CourseListItem,
    CourseObservationReadItem,
    CourseTaskDetails,
    CourseTaskObservationReadItem,
    CourseTaskReadItem,
)
from backend.context.course.application.use_cases.update_course_status import (
    UpdateCourseStatusAction,
)
from backend.context.course.application.use_cases.update_course_task_status import (
    UpdateCourseTaskStatusAction,
)
from backend.context.course.domain.value_objects.course_status import CourseStatus
from backend.context.course.domain.value_objects.course_task_status import (
    CourseTaskStatus,
)


class CourseListItemResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    description: str | None
    status: CourseStatus

    @classmethod
    def from_read_model(
        cls,
        item: CourseListItem,
    ) -> "CourseListItemResponse":
        return cls(
            id=item.id,
            user_id=item.user_id,
            title=item.title,
            description=item.description,
            status=item.status,
        )


class CourseObservationResponse(BaseModel):
    id: UUID
    title: str
    description: str | None

    @classmethod
    def from_read_model(
        cls,
        item: CourseObservationReadItem,
    ) -> "CourseObservationResponse":
        return cls(
            id=item.id,
            title=item.title,
            description=item.description,
        )


class CourseTaskResponse(BaseModel):
    id: UUID
    course_id: UUID
    title: str
    description: str | None
    priority: int
    status: CourseTaskStatus

    @classmethod
    def from_read_model(
        cls,
        item: CourseTaskReadItem,
    ) -> "CourseTaskResponse":
        return cls(
            id=item.id,
            course_id=item.course_id,
            title=item.title,
            description=item.description,
            priority=item.priority,
            status=item.status,
        )


class CourseResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    description: str | None
    status: CourseStatus
    observations: list[CourseObservationResponse] | None = None
    tasks: list[CourseTaskResponse] | None = None

    @classmethod
    def from_read_model(
        cls,
        course: CourseDetails,
    ) -> "CourseResponse":
        return cls(
            id=course.id,
            user_id=course.user_id,
            title=course.title,
            description=course.description,
            status=course.status,
            observations=(
                [
                    CourseObservationResponse.from_read_model(observation)
                    for observation in course.observations
                ]
                if course.observations is not None
                else None
            ),
            tasks=(
                [
                    CourseTaskResponse.from_read_model(task)
                    for task in course.tasks
                ]
                if course.tasks is not None
                else None
            ),
        )


class CourseTaskObservationResponse(BaseModel):
    id: UUID
    title: str
    description: str | None

    @classmethod
    def from_read_model(
        cls,
        item: CourseTaskObservationReadItem,
    ) -> "CourseTaskObservationResponse":
        return cls(
            id=item.id,
            title=item.title,
            description=item.description,
        )


class CourseTaskDetailsResponse(BaseModel):
    id: UUID
    course_id: UUID
    title: str
    description: str | None
    priority: int
    status: CourseTaskStatus
    observations: list[CourseTaskObservationResponse] | None = None

    @classmethod
    def from_read_model(
        cls,
        task: CourseTaskDetails,
    ) -> "CourseTaskDetailsResponse":
        return cls(
            id=task.id,
            course_id=task.course_id,
            title=task.title,
            description=task.description,
            priority=task.priority,
            status=task.status,
            observations=(
                [
                    CourseTaskObservationResponse.from_read_model(observation)
                    for observation in task.observations
                ]
                if task.observations is not None
                else None
            ),
        )


class ReadCoursesResponse(BaseModel):
    courses: list[CourseListItemResponse]


class ReadCourseResponse(BaseModel):
    course: CourseResponse | None


class ReadCourseTaskResponse(BaseModel):
    task: CourseTaskDetailsResponse | None


class CreateCourseRequest(BaseModel):
    user_id: UUID
    title: str = Field(min_length=1)
    description: str | None = None


class CreateCourseResponse(BaseModel):
    course_id: UUID


class CreateCourseTaskRequest(BaseModel):
    title: str = Field(min_length=1)
    description: str | None = None
    priority: int | None = Field(default=None, ge=1, le=3)


class CreateCourseTaskResponse(BaseModel):
    task_id: UUID


class CreateCourseObservationRequest(BaseModel):
    title: str = Field(min_length=1)
    description: str | None = None


class CreateCourseObservationResponse(BaseModel):
    observation_id: UUID


class CreateCourseTaskObservationRequest(BaseModel):
    title: str = Field(min_length=1)
    description: str | None = None


class CreateCourseTaskObservationResponse(BaseModel):
    observation_id: UUID


class UpdateCourseStatusRequest(BaseModel):
    action: UpdateCourseStatusAction


class UpdateCourseStatusResponse(BaseModel):
    course_id: UUID


class UpdateCourseTaskStatusRequest(BaseModel):
    action: UpdateCourseTaskStatusAction


class UpdateCourseTaskStatusResponse(BaseModel):
    task_id: UUID