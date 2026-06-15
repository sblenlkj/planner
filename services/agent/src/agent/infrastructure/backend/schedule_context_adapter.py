from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime
from typing import Any
from uuid import UUID

from agent.application.dto.schedule import (
    DeadlineDto,
    ReminderDto,
    ScheduleDateObservationDto,
    ScheduleDayObservationDto,
)
from agent.application.ports.schedule_context import ScheduleContextPort
from agent.core.backend_settings import BackendApiSettings
from agent.infrastructure.backend.http_client import BackendHttpClient
from .parsing import extract_created_id

class HttpScheduleContextAdapter(ScheduleContextPort):
    """HTTP adapter for Backend schedule context.

    MVP scope:
      - no weekly template;
      - date observations;
      - day observations;
      - reminders/deadlines through commitments.
    """

    def __init__(
        self,
        *,
        client: BackendHttpClient,
        settings: BackendApiSettings,
    ) -> None:
        self._client = client
        self._settings = settings

    async def list_schedule_date_observations(
        self,
        user_id: UUID,
        *,
        date_: date,
    ) -> list[ScheduleDateObservationDto]:
        payload = await self._client.get_json(
            self._settings.list_schedule_date_observations_path,
            params={
                "user_id": str(user_id),
                "date": date_.isoformat(),
            },
        )

        items = _extract_items(
            payload,
            keys=(
                "observations",
                "date_observations",
                "schedule_date_observations",
                "items",
                "data",
            ),
        )
        return [ScheduleDateObservationDto.from_api(item) for item in items]

    async def create_schedule_date_observation(
        self,
        user_id: UUID,
        *,
        starts_on: date,
        description: str,
        ends_on: date | None = None,
    ) -> ScheduleDateObservationDto:
        payload = await self._client.post_json(
            self._settings.create_schedule_date_observation_path,
            json={
                "user_id": str(user_id),
                "starts_on": starts_on.isoformat(),
                "ends_on": ends_on.isoformat() if ends_on is not None else None,
                "description": description,
            },
        )

        observation_id = extract_created_id(payload, "observation_id", "id")

        return ScheduleDateObservationDto(
            id=observation_id,
            user_id=user_id,
            starts_on=starts_on,
            ends_on=ends_on,
            description=description,
        )

    async def list_schedule_day_observations(
        self,
        user_id: UUID,
        *,
        date_: date,
    ) -> list[ScheduleDayObservationDto]:
        payload = await self._client.get_json(
            self._settings.list_schedule_day_observations_path,
            params={
                "user_id": str(user_id),
                "date": date_.isoformat(),
            },
        )

        items = _extract_items(
            payload,
            keys=(
                "observations",
                "day_observations",
                "schedule_day_observations",
                "items",
                "data",
            ),
        )
        return [ScheduleDayObservationDto.from_api(item) for item in items]

    async def create_schedule_day_observation(
        self,
        user_id: UUID,
        *,
        date_: date,
        description: str,
    ) -> ScheduleDayObservationDto:
        payload = await self._client.post_json(
            self._settings.create_schedule_day_observation_path,
            json={
                "user_id": str(user_id),
                "date": date_.isoformat(),
                "description": description,
            },
        )

        observation_id = extract_created_id(payload, "observation_id", "id")

        return ScheduleDayObservationDto(
            id=observation_id,
            user_id=user_id,
            date=date_,
            description=description,
        )

    async def list_commitments(
        self,
        user_id: UUID,
    ) -> list[ReminderDto | DeadlineDto]:
        payload = await self._client.get_json(
            self._settings.list_commitments_path,
            params={
                "user_id": str(user_id),
            },
        )

        if not isinstance(payload, Mapping):
            raise TypeError(f"Unexpected commitments payload shape: {payload!r}")

        reminders_payload = payload.get("reminders", [])
        deadlines_payload = payload.get("deadlines", [])

        if not isinstance(reminders_payload, list):
            raise TypeError(f"Unexpected reminders payload shape: {reminders_payload!r}")

        if not isinstance(deadlines_payload, list):
            raise TypeError(f"Unexpected deadlines payload shape: {deadlines_payload!r}")

        result: list[ReminderDto | DeadlineDto] = []

        for item in reminders_payload:
            result.append(ReminderDto.from_api(_ensure_mapping(item)))

        for item in deadlines_payload:
            result.append(DeadlineDto.from_api(_ensure_mapping(item)))

        return result

    async def create_reminder(
        self,
        user_id: UUID,
        *,
        remind_at: datetime,
        title: str,
        description: str | None = None,
    ) -> ReminderDto:
        payload = await self._client.post_json(
            self._settings.create_reminder_path,
            json={
                "user_id": str(user_id),
                "remind_at_local": remind_at.isoformat(),
                "title": title,
                "description": description,
            },
        )

        reminder_id = extract_created_id(payload, "reminder_id", "commitment_id", "id")

        return ReminderDto(
            id=reminder_id,
            user_id=user_id,
            remind_at=remind_at,
            title=title,
            description=description,
            status="active",
        )

    async def create_deadline(
        self,
        user_id: UUID,
        *,
        due_at: datetime,
        title: str,
        description: str | None = None,
        course_id: UUID | None = None,
        course_task_id: UUID | None = None,
    ) -> DeadlineDto:
        payload = await self._client.post_json(
            self._settings.create_deadline_path,
            json={
                "user_id": str(user_id),
                "due_at": due_at.isoformat(),
                "title": title,
                "description": description,
                "course_id": str(course_id) if course_id is not None else None,
                "course_task_id": str(course_task_id) if course_task_id is not None else None,
            },
        )

        deadline_id = extract_created_id(payload, "deadline_id", "commitment_id", "id")

        return DeadlineDto(
            id=deadline_id,
            user_id=user_id,
            due_at=due_at,
            title=title,
            description=description,
            status="active",
            course_id=course_id,
            course_task_id=course_task_id,
        )


def _extract_items(payload: Any, *, keys: tuple[str, ...]) -> list[Mapping[str, Any]]:
    if payload is None:
        return []

    if isinstance(payload, list):
        return [_ensure_mapping(item) for item in payload]

    if isinstance(payload, Mapping):
        for key in keys:
            value = payload.get(key)
            if isinstance(value, list):
                return [_ensure_mapping(item) for item in value]

    raise TypeError(f"Unexpected schedule list payload shape: {payload!r}")


def _extract_single(payload: Any, *, keys: tuple[str, ...]) -> Mapping[str, Any]:
    if isinstance(payload, Mapping):
        for key in keys:
            value = payload.get(key)
            if value is not None:
                return _ensure_mapping(value)

        if "id" in payload:
            return payload

    raise TypeError(f"Unexpected schedule single payload shape: {payload!r}")


def _ensure_mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value

    raise TypeError(f"Expected mapping payload item, got {type(value)!r}: {value!r}")