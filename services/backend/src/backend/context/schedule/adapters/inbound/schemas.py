from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from backend.context.schedule.domain.commitment.value_objects.commitment_status import (
    CommitmentStatus,
)


class CreateReminderRequest(BaseModel):
    user_id: UUID
    remind_at_local: datetime
    title: str = Field(min_length=1)
    description: str | None = None


class CreateReminderResponse(BaseModel):
    reminder_id: UUID


class CreateDeadlineRequest(BaseModel):
    user_id: UUID
    due_at: datetime
    title: str = Field(min_length=1)
    description: str | None = None


class CreateDeadlineResponse(BaseModel):
    deadline_id: UUID


class ReminderResponse(BaseModel):
    id: UUID
    user_id: UUID
    remind_at: datetime
    title: str
    description: str | None
    status: CommitmentStatus


class DeadlineResponse(BaseModel):
    id: UUID
    user_id: UUID
    due_at: datetime
    title: str
    description: str | None
    status: CommitmentStatus


class ListCommitmentsResponse(BaseModel):
    reminders: list[ReminderResponse]
    deadlines: list[DeadlineResponse]


class CreateScheduleDateObservationRequest(BaseModel):
    user_id: UUID
    starts_on: date
    description: str = Field(min_length=1)
    ends_on: date | None = None


class CreateScheduleDateObservationResponse(BaseModel):
    observation_id: UUID


class ScheduleDateObservationResponse(BaseModel):
    id: UUID
    user_id: UUID
    starts_on: date
    ends_on: date | None
    description: str


class ListScheduleDateObservationsResponse(BaseModel):
    observations: list[ScheduleDateObservationResponse]


class CreateScheduleDayObservationRequest(BaseModel):
    user_id: UUID
    date: date
    description: str = Field(min_length=1)


class CreateScheduleDayObservationResponse(BaseModel):
    observation_id: UUID


class ScheduleDayObservationResponse(BaseModel):
    id: UUID
    user_id: UUID
    date: date
    description: str


class ListScheduleDayObservationsResponse(BaseModel):
    observations: list[ScheduleDayObservationResponse]