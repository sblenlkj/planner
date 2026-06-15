from __future__ import annotations

from typing import Annotated
from uuid import UUID

from direttore import ModularDirettoreWithSimpleSession
from fastapi import APIRouter, Depends

from backend.bootstrap.direttore import get_direttore
from backend.context.course.adapters.inbound.schemas import (
    CourseListItemResponse,
    CourseResponse,
    CourseTaskDetailsResponse,
    CreateCourseObservationRequest,
    CreateCourseObservationResponse,
    CreateCourseRequest,
    CreateCourseResponse,
    CreateCourseTaskObservationRequest,
    CreateCourseTaskObservationResponse,
    CreateCourseTaskRequest,
    CreateCourseTaskResponse,
    ReadCourseResponse,
    ReadCourseTaskResponse,
    ReadCoursesResponse,
    UpdateCourseStatusRequest,
    UpdateCourseStatusResponse,
    UpdateCourseTaskStatusRequest,
    UpdateCourseTaskStatusResponse,
)
from backend.context.course.application.use_cases import (
    CreateCourseCommand,
    CreateCourseCommandResult,
    CreateCourseObservationCommand,
    CreateCourseObservationCommandResult,
    CreateCourseTaskCommand,
    CreateCourseTaskCommandResult,
    CreateCourseTaskObservationCommand,
    CreateCourseTaskObservationCommandResult,
    ReadCourseCommand,
    ReadCourseCommandResult,
    ReadCoursesCommand,
    ReadCoursesCommandResult,
    ReadCourseTaskCommand,
    ReadCourseTaskCommandResult,
    UpdateCourseStatusCommand,
    UpdateCourseStatusCommandResult,
    UpdateCourseTaskStatusCommand,
    UpdateCourseTaskStatusCommandResult,
)
from backend.context.course.domain.value_objects.course_status import CourseStatus
from backend.context.course.domain.value_objects.course_task_status import (
    CourseTaskStatus,
)


router = APIRouter(
    prefix="/courses",
    tags=["course"],
)

DirettoreDep = Annotated[
    ModularDirettoreWithSimpleSession,
    Depends(get_direttore),
]


@router.get(
    "",
    response_model=ReadCoursesResponse,
)
async def read_courses(
    user_id: UUID,
    direttore: DirettoreDep,
    status: CourseStatus | None = None,
) -> ReadCoursesResponse:
    result = await direttore.handle(
        ReadCoursesCommand(
            user_id=user_id,
            status=status,
        )
    )

    if not isinstance(result, ReadCoursesCommandResult):
        raise TypeError(
            "ReadCoursesCommand returned unexpected result type. "
            f"Got {type(result).__module__}.{type(result).__qualname__}."
        )

    return ReadCoursesResponse(
        courses=[
            CourseListItemResponse.from_read_model(course)
            for course in result.courses
        ]
    )


@router.get(
    "/{course_id}",
    response_model=ReadCourseResponse,
)
async def read_course(
    course_id: UUID,
    direttore: DirettoreDep,
    with_observations: bool = False,
    with_tasks: bool = True,
    task_status: CourseTaskStatus | None = None,
) -> ReadCourseResponse:
    result = await direttore.handle(
        ReadCourseCommand(
            course_id=course_id,
            with_observations=with_observations,
            with_tasks=with_tasks,
            task_status=task_status,
        )
    )

    if not isinstance(result, ReadCourseCommandResult):
        raise TypeError(
            "ReadCourseCommand returned unexpected result type. "
            f"Got {type(result).__module__}.{type(result).__qualname__}."
        )

    return ReadCourseResponse(
        course=(
            CourseResponse.from_read_model(result.course)
            if result.course is not None
            else None
        )
    )


@router.get(
    "/tasks/{task_id}",
    response_model=ReadCourseTaskResponse,
)
async def read_course_task(
    task_id: UUID,
    direttore: DirettoreDep,
    with_observations: bool = False,
) -> ReadCourseTaskResponse:
    result = await direttore.handle(
        ReadCourseTaskCommand(
            task_id=task_id,
            with_observations=with_observations,
        )
    )

    if not isinstance(result, ReadCourseTaskCommandResult):
        raise TypeError(
            "ReadCourseTaskCommand returned unexpected result type. "
            f"Got {type(result).__module__}.{type(result).__qualname__}."
        )

    return ReadCourseTaskResponse(
        task=(
            CourseTaskDetailsResponse.from_read_model(result.task)
            if result.task is not None
            else None
        )
    )


@router.post(
    "",
    response_model=CreateCourseResponse,
)
async def create_course(
    request: CreateCourseRequest,
    direttore: DirettoreDep,
) -> CreateCourseResponse:
    result = await direttore.handle(
        CreateCourseCommand(
            user_id=request.user_id,
            title=request.title,
            description=request.description,
        )
    )

    if not isinstance(result, CreateCourseCommandResult):
        raise TypeError(
            "CreateCourseCommand returned unexpected result type. "
            f"Got {type(result).__module__}.{type(result).__qualname__}."
        )

    return CreateCourseResponse(course_id=result.course_id)


@router.post(
    "/{course_id}/tasks",
    response_model=CreateCourseTaskResponse,
)
async def create_course_task(
    course_id: UUID,
    request: CreateCourseTaskRequest,
    direttore: DirettoreDep,
) -> CreateCourseTaskResponse:
    result = await direttore.handle(
        CreateCourseTaskCommand(
            course_id=course_id,
            title=request.title,
            description=request.description,
            priority=request.priority,
        )
    )

    if not isinstance(result, CreateCourseTaskCommandResult):
        raise TypeError(
            "CreateCourseTaskCommand returned unexpected result type. "
            f"Got {type(result).__module__}.{type(result).__qualname__}."
        )

    return CreateCourseTaskResponse(task_id=result.task_id)


@router.post(
    "/{course_id}/observations",
    response_model=CreateCourseObservationResponse,
)
async def create_course_observation(
    course_id: UUID,
    request: CreateCourseObservationRequest,
    direttore: DirettoreDep,
) -> CreateCourseObservationResponse:
    result = await direttore.handle(
        CreateCourseObservationCommand(
            course_id=course_id,
            title=request.title,
            description=request.description,
        )
    )

    if not isinstance(result, CreateCourseObservationCommandResult):
        raise TypeError(
            "CreateCourseObservationCommand returned unexpected result type. "
            f"Got {type(result).__module__}.{type(result).__qualname__}."
        )

    return CreateCourseObservationResponse(
        observation_id=result.observation_id,
    )


@router.post(
    "/tasks/{task_id}/observations",
    response_model=CreateCourseTaskObservationResponse,
)
async def create_course_task_observation(
    task_id: UUID,
    request: CreateCourseTaskObservationRequest,
    direttore: DirettoreDep,
) -> CreateCourseTaskObservationResponse:
    result = await direttore.handle(
        CreateCourseTaskObservationCommand(
            task_id=task_id,
            title=request.title,
            description=request.description,
        )
    )

    if not isinstance(result, CreateCourseTaskObservationCommandResult):
        raise TypeError(
            "CreateCourseTaskObservationCommand returned unexpected result "
            "type. "
            f"Got {type(result).__module__}.{type(result).__qualname__}."
        )

    return CreateCourseTaskObservationResponse(
        observation_id=result.observation_id,
    )


@router.patch(
    "/{course_id}/status",
    response_model=UpdateCourseStatusResponse,
)
async def update_course_status(
    course_id: UUID,
    request: UpdateCourseStatusRequest,
    direttore: DirettoreDep,
) -> UpdateCourseStatusResponse:
    result = await direttore.handle(
        UpdateCourseStatusCommand(
            course_id=course_id,
            action=request.action,
        )
    )

    if not isinstance(result, UpdateCourseStatusCommandResult):
        raise TypeError(
            "UpdateCourseStatusCommand returned unexpected result type. "
            f"Got {type(result).__module__}.{type(result).__qualname__}."
        )

    return UpdateCourseStatusResponse(course_id=result.course_id)


@router.patch(
    "/tasks/{task_id}/status",
    response_model=UpdateCourseTaskStatusResponse,
)
async def update_course_task_status(
    task_id: UUID,
    request: UpdateCourseTaskStatusRequest,
    direttore: DirettoreDep,
) -> UpdateCourseTaskStatusResponse:
    result = await direttore.handle(
        UpdateCourseTaskStatusCommand(
            task_id=task_id,
            action=request.action,
        )
    )

    if not isinstance(result, UpdateCourseTaskStatusCommandResult):
        raise TypeError(
            "UpdateCourseTaskStatusCommand returned unexpected result type. "
            f"Got {type(result).__module__}.{type(result).__qualname__}."
        )

    return UpdateCourseTaskStatusResponse(task_id=result.task_id)