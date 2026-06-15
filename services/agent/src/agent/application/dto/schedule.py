from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
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


def _date(value: Any) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    return date.fromisoformat(str(value))


def _optional_date(value: Any) -> date | None:
    if value is None:
        return None
    return _date(value)


def _datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _optional_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    return _datetime(value)


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


@dataclass(frozen=True, slots=True)
class ScheduleDateObservationDto:
    id: UUID
    user_id: UUID
    starts_on: date
    ends_on: date | None
    description: str

    @classmethod
    def from_api(cls, data: Mapping[str, Any]) -> "ScheduleDateObservationDto":
        return cls(
            id=_uuid(data["id"]),
            user_id=_uuid(data["user_id"]),
            starts_on=_date(data["starts_on"]),
            ends_on=_optional_date(data.get("ends_on")),
            description=str(data["description"]),
        )


@dataclass(frozen=True, slots=True)
class ScheduleDayObservationDto:
    id: UUID
    user_id: UUID
    date: date
    description: str

    @classmethod
    def from_api(cls, data: Mapping[str, Any]) -> "ScheduleDayObservationDto":
        return cls(
            id=_uuid(data["id"]),
            user_id=_uuid(data["user_id"]),
            date=_date(data["date"]),
            description=str(data["description"]),
        )


@dataclass(frozen=True, slots=True)
class ReminderDto:
    id: UUID
    user_id: UUID
    remind_at: datetime
    title: str
    description: str | None
    status: str

    @classmethod
    def from_api(cls, data: Mapping[str, Any]) -> "ReminderDto":
        return cls(
            id=_uuid(data["id"]),
            user_id=_uuid(data["user_id"]),
            remind_at=_datetime(data["remind_at"]),
            title=str(data["title"]),
            description=_optional_str(data.get("description")),
            status=str(data.get("status", "active")),
        )


@dataclass(frozen=True, slots=True)
class DeadlineDto:
    id: UUID
    user_id: UUID
    due_at: datetime
    title: str
    description: str | None
    status: str
    course_id: UUID | None
    course_task_id: UUID | None

    @classmethod
    def from_api(cls, data: Mapping[str, Any]) -> "DeadlineDto":
        return cls(
            id=_uuid(data["id"]),
            user_id=_uuid(data["user_id"]),
            due_at=_datetime(data["due_at"]),
            title=str(data["title"]),
            description=_optional_str(data.get("description")),
            status=str(data.get("status", "active")),
            course_id=_optional_uuid(data.get("course_id")),
            course_task_id=_optional_uuid(data.get("course_task_id")),
        )