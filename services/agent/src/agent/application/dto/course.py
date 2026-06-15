from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
from uuid import UUID


def _uuid(value: Any) -> UUID:
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


def _optional_uuid(value: Any) -> UUID | None:
    if value is None:
        return None
    return _uuid(value)


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


@dataclass(frozen=True, slots=True)
class CourseObservationDto:
    id: UUID
    course_id: UUID
    title: str | None
    description: str

    @classmethod
    def from_api(cls, data: Mapping[str, Any]) -> "CourseObservationDto":
        return cls(
            id=_uuid(data["id"]),
            course_id=_uuid(data["course_id"]),
            title=_optional_str(data.get("title")),
            description=str(data["description"]),
        )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "CourseObservationDto":
        return cls.from_api(data)


@dataclass(frozen=True, slots=True)
class CourseTaskObservationDto:
    id: UUID
    task_id: UUID
    title: str | None
    description: str
    progress: int | None

    @classmethod
    def from_api(cls, data: Mapping[str, Any]) -> "CourseTaskObservationDto":
        return cls(
            id=_uuid(data["id"]),
            task_id=_uuid(data["task_id"]),
            title=_optional_str(data.get("title")),
            description=str(data["description"]),
            progress=_optional_int(data.get("progress")),
        )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "CourseTaskObservationDto":
        return cls.from_api(data)


@dataclass(frozen=True, slots=True)
class CourseTaskDto:
    id: UUID
    course_id: UUID
    title: str
    description: str | None
    priority: int | None
    status: str | None
    progress: int | None
    next_task_id: UUID | None
    observations: tuple[CourseTaskObservationDto, ...] = ()

    @classmethod
    def from_api(cls, data: Mapping[str, Any]) -> "CourseTaskDto":
        observations_payload = data.get("observations") or ()
        observations = tuple(
            CourseTaskObservationDto.from_api(item)
            for item in observations_payload
        )

        return cls(
            id=_uuid(data["id"]),
            course_id=_uuid(data["course_id"]),
            title=str(data["title"]),
            description=_optional_str(data.get("description")),
            priority=_optional_int(data.get("priority")),
            status=_optional_str(data.get("status")),
            progress=_optional_int(data.get("progress")),
            next_task_id=_optional_uuid(data.get("next_task_id")),
            observations=observations,
        )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "CourseTaskDto":
        return cls.from_api(data)


@dataclass(frozen=True, slots=True)
class CourseDto:
    id: UUID
    user_id: UUID
    title: str
    description: str | None
    status: str | None
    tasks: tuple[CourseTaskDto, ...] = ()
    observations: tuple[CourseObservationDto, ...] = ()

    @classmethod
    def from_api(cls, data: Mapping[str, Any]) -> "CourseDto":
        # Backend GET /courses/{course_id} currently returns:
        # {
        #   "course": {
        #      ...
        #      "tasks": [...],
        #      "observations": ...
        #   }
        # }
        #
        # Some adapters may pass either the whole payload or the nested course.
        course_data = data.get("course") if isinstance(data.get("course"), Mapping) else data

        tasks_payload = course_data.get("tasks") or ()
        observations_payload = course_data.get("observations") or ()

        tasks = tuple(CourseTaskDto.from_api(item) for item in tasks_payload)
        observations = tuple(
            CourseObservationDto.from_api(item)
            for item in observations_payload
        )

        return cls(
            id=_uuid(course_data["id"]),
            user_id=_uuid(course_data["user_id"]),
            title=str(course_data["title"]),
            description=_optional_str(course_data.get("description")),
            status=_optional_str(course_data.get("status")),
            tasks=tasks,
            observations=observations,
        )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "CourseDto":
        return cls.from_api(data)