from __future__ import annotations

from typing import Any
from uuid import UUID

from agent.application.dto import (
    CourseDto,
    CourseObservationDto,
    CourseTaskDto,
    CourseTaskObservationDto,
)
from agent.application.ports import CourseContextPort
from agent.core.backend_settings import BackendApiSettings

from .http_client import BackendHttpClient
from .parsing import (
    as_int_or_none,
    as_optional_uuid,
    as_uuid,
    extract_created_id,
    require_mapping,
    unwrap_items,
)


class HttpCourseContextAdapter(CourseContextPort):
    def __init__(self, *, client: BackendHttpClient, settings: BackendApiSettings) -> None:
        self._client = client
        self._settings = settings

    async def list_courses(self, user_id: UUID) -> list[CourseDto]:
        payload = await self._client.get_json(
            self._settings.list_courses_path,
            params={"user_id": str(user_id)},
        )

        return [
            CourseDto.from_api(require_mapping(item))
            for item in unwrap_items(payload, "courses")
        ]

    async def get_course(
        self,
        course_id: UUID,
        *,
        with_observations: bool = False,
        with_tasks: bool = True,
        task_status: str | None = None,
    ) -> CourseDto:
        path = self._settings.get_course_path.format(course_id=course_id)

        params: dict[str, Any] = {
            "with_observations": with_observations,
            "with_tasks": with_tasks,
        }

        if task_status is not None:
            params["task_status"] = task_status

        payload = await self._client.get_json(path, params=params)

        return CourseDto.from_api(require_mapping(payload))

    async def list_course_tasks(self, course_id: UUID) -> list[CourseTaskDto]:
        path = self._settings.list_course_tasks_path.format(course_id=course_id)
        payload = await self._client.get_json(path)

        return [
            _parse_course_task(require_mapping(item), fallback_course_id=course_id)
            for item in unwrap_items(payload, "tasks", "course_tasks")
        ]

    async def get_course_task(self, task_id: UUID) -> CourseTaskDto:
        path = self._settings.get_course_task_path.format(task_id=task_id)
        payload = await self._client.get_json(path)

        return _parse_course_task(require_mapping(payload))

    async def list_course_observations(
        self,
        course_id: UUID,
    ) -> list[CourseObservationDto]:
        path = self._settings.list_course_observations_path.format(course_id=course_id)
        payload = await self._client.get_json(path)

        return [
            _parse_course_observation(require_mapping(item), fallback_course_id=course_id)
            for item in unwrap_items(payload, "observations", "course_observations")
        ]

    async def list_course_task_observations(
        self,
        task_id: UUID,
    ) -> list[CourseTaskObservationDto]:
        path = self._settings.list_course_task_observations_path.format(task_id=task_id)
        payload = await self._client.get_json(path)

        return [
            _parse_course_task_observation(require_mapping(item), fallback_task_id=task_id)
            for item in unwrap_items(
                payload,
                "observations",
                "task_observations",
                "course_task_observations",
            )
        ]

    async def create_course(
        self,
        user_id: UUID,
        *,
        title: str,
        description: str | None = None,
    ) -> CourseDto:
        payload = await self._client.post_json(
            self._settings.create_course_path,
            json={
                "user_id": str(user_id),
                "title": title,
                "description": description,
            },
        )

        course_id = extract_created_id(payload, "course_id", "id")

        return CourseDto(
            id=course_id,
            user_id=user_id,
            title=title,
            description=description,
            status="active",
            tasks=(),
            observations=(),
        )

    async def create_course_task(
        self,
        course_id: UUID,
        *,
        title: str,
        description: str | None = None,
        priority: int = 2,
    ) -> CourseTaskDto:
        payload = await self._client.post_json(
            self._settings.create_course_task_path.format(course_id=course_id),
            json={
                "title": title,
                "description": description,
                "priority": priority,
            },
        )

        task_id = extract_created_id(payload, "task_id", "id")

        return CourseTaskDto(
            id=task_id,
            course_id=course_id,
            title=title,
            description=description,
            priority=priority,
            status="pending",
            progress=0,
            next_task_id=None,
            observations=(),
        )

    async def update_course_task_progress(
        self,
        task_id: UUID,
        *,
        progress: int,
    ) -> CourseTaskDto:
        path = self._settings.update_course_task_progress_path.format(task_id=task_id)
        payload = await self._client.patch_json(path, json={"progress": progress})

        return _parse_course_task(require_mapping(payload))

    async def create_course_observation(
        self,
        course_id: UUID,
        *,
        title: str,
        description: str,
    ) -> CourseObservationDto:
        payload = await self._client.post_json(
            self._settings.create_course_observation_path.format(course_id=course_id),
            json={
                "title": title,
                "description": description,
            },
        )

        observation_id = extract_created_id(payload, "observation_id", "id")

        return CourseObservationDto(
            id=observation_id,
            course_id=course_id,
            title=title,
            description=description,
        )

    async def create_course_task_observation(
        self,
        task_id: UUID,
        *,
        title: str,
        description: str,
        progress: int | None = None,
    ) -> CourseTaskObservationDto:
        payload = await self._client.post_json(
            self._settings.create_course_task_observation_path.format(task_id=task_id),
            json={
                "title": title,
                "description": description,
                "progress": progress,
            },
        )

        observation_id = extract_created_id(payload, "observation_id", "id")

        return CourseTaskObservationDto(
            id=observation_id,
            task_id=task_id,
            title=title,
            description=description,
            progress=progress,
        )


def _parse_course_task(
    payload: dict[str, Any],
    *,
    fallback_course_id: UUID | None = None,
) -> CourseTaskDto:
    return CourseTaskDto(
        id=as_uuid(
            payload.get("id")
            or payload.get("task_id")
            or payload.get("course_task_id"),
            field="task_id",
        ),
        course_id=as_uuid(
            payload.get("course_id") or fallback_course_id,
            field="course_id",
        ),
        title=str(payload.get("title") or payload.get("name") or ""),
        description=payload.get("description"),
        priority=as_int_or_none(payload.get("priority")),
        status=payload.get("status"),
        progress=as_int_or_none(payload.get("progress")),
        next_task_id=as_optional_uuid(
            payload.get("next_task_id"),
            field="next_task_id",
        ),
        observations=tuple(
            _parse_course_task_observation(require_mapping(item))
            for item in (payload.get("observations") or ())
        ),
    )


def _parse_course_observation(
    payload: dict[str, Any],
    *,
    fallback_course_id: UUID | None = None,
) -> CourseObservationDto:
    return CourseObservationDto(
        id=as_uuid(
            payload.get("id") or payload.get("observation_id"),
            field="observation_id",
        ),
        course_id=as_uuid(
            payload.get("course_id") or fallback_course_id,
            field="course_id",
        ),
        title=str(payload.get("title") or ""),
        description=str(payload.get("description") or ""),
    )


def _parse_course_task_observation(
    payload: dict[str, Any],
    *,
    fallback_task_id: UUID | None = None,
) -> CourseTaskObservationDto:
    return CourseTaskObservationDto(
        id=as_uuid(
            payload.get("id") or payload.get("observation_id"),
            field="observation_id",
        ),
        task_id=as_uuid(
            payload.get("task_id")
            or payload.get("course_task_id")
            or fallback_task_id,
            field="task_id",
        ),
        title=str(payload.get("title") or ""),
        description=str(payload.get("description") or ""),
        progress=as_int_or_none(payload.get("progress")),
    )