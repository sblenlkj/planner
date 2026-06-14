from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from direttore import AbstractQueryHandler, Query

from backend.context.schedule.application.orchestration import (
    ScheduleQueryHandlerContext,
    query_handler_registry,
)
from backend.context.schedule.domain.commitment.entities.deadline import Deadline
from backend.context.schedule.domain.commitment.entities.reminder import Reminder
from backend.context.schedule.domain.commitment.value_objects.commitment_status import (
    CommitmentStatus,
)


class CommitmentKindFilter(StrEnum):
    REMINDER = "reminder"
    DEADLINE = "deadline"


@dataclass(frozen=True, kw_only=True)
class CommitmentReminderReadModel:
    id: UUID
    user_id: UUID
    remind_at: datetime
    title: str
    description: str | None
    status: CommitmentStatus


@dataclass(frozen=True, kw_only=True)
class CommitmentDeadlineReadModel:
    id: UUID
    user_id: UUID
    due_at: datetime
    title: str
    description: str | None
    status: CommitmentStatus


@dataclass(frozen=True, kw_only=True)
class ListUserCommitmentsQuery(Query):
    user_id: UUID
    status: CommitmentStatus | None = None
    kind: CommitmentKindFilter | None = None


@dataclass(frozen=True, kw_only=True)
class ListUserCommitmentsQueryResult:
    reminders: list[CommitmentReminderReadModel]
    deadlines: list[CommitmentDeadlineReadModel]


@query_handler_registry.handler(ListUserCommitmentsQuery)
class ListUserCommitmentsQueryHandler(AbstractQueryHandler):
    async def __call__(
        self,
        query: ListUserCommitmentsQuery,
        context: ScheduleQueryHandlerContext,
    ) -> ListUserCommitmentsQueryResult:
        reminders: list[Reminder] = []
        deadlines: list[Deadline] = []

        if query.kind is None or query.kind == CommitmentKindFilter.REMINDER:
            reminders = await context.uow.commitment_reader.list_reminders(
                user_id=query.user_id,
                status=query.status,
            )

        if query.kind is None or query.kind == CommitmentKindFilter.DEADLINE:
            deadlines = await context.uow.commitment_reader.list_deadlines(
                user_id=query.user_id,
                status=query.status,
            )

        return ListUserCommitmentsQueryResult(
            reminders=[self._map_reminder(reminder) for reminder in reminders],
            deadlines=[self._map_deadline(deadline) for deadline in deadlines],
        )

    @staticmethod
    def _map_reminder(reminder: Reminder) -> CommitmentReminderReadModel:
        return CommitmentReminderReadModel(
            id=reminder.id,
            user_id=reminder.user_id,
            remind_at=reminder.remind_at,
            title=reminder.title,
            description=reminder.description,
            status=reminder.status,
        )

    @staticmethod
    def _map_deadline(deadline: Deadline) -> CommitmentDeadlineReadModel:
        return CommitmentDeadlineReadModel(
            id=deadline.id,
            user_id=deadline.user_id,
            due_at=deadline.due_at,
            title=deadline.title,
            description=deadline.description,
            status=deadline.status,
        )