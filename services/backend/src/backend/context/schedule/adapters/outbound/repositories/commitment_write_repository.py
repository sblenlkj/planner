from __future__ import annotations

from uuid import UUID

from sqlalchemy import select, update as update_sql
from sqlalchemy.ext.asyncio import AsyncSession

from backend.context.schedule.adapters.outbound.models import DeadlineRow, ReminderRow
from backend.context.schedule.application.ports.repositories.commitment_write_repository import (
    CommitmentWriteRepository,
)
from backend.context.schedule.domain.commitment.entities.deadline import Deadline
from backend.context.schedule.domain.commitment.entities.reminder import Reminder
from backend.context.schedule.domain.commitment.value_objects.commitment_status import (
    CommitmentStatus,
)


class SqlAlchemyCommitmentWriteRepository(CommitmentWriteRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_reminder(self, *, reminder: Reminder) -> None:
        self._session.add(self._to_reminder_row(reminder))

    async def get_reminder_by_id(self, reminder_id: UUID) -> Reminder | None:
        result = await self._session.execute(
            select(ReminderRow).where(ReminderRow.id == reminder_id)
        )
        row = result.scalar_one_or_none()

        if row is None:
            return None

        return self._to_reminder(row)

    async def update_reminder(self, *, reminder: Reminder) -> None:
        await self._session.execute(
            update_sql(ReminderRow)
            .where(ReminderRow.id == reminder.id)
            .values(
                user_id=reminder.user_id,
                remind_at=reminder.remind_at,
                title=reminder.title,
                description=reminder.description,
                status=reminder.status.value,
            )
        )

    async def add_deadline(self, *, deadline: Deadline) -> None:
        self._session.add(self._to_deadline_row(deadline))

    async def get_deadline_by_id(self, deadline_id: UUID) -> Deadline | None:
        result = await self._session.execute(
            select(DeadlineRow).where(DeadlineRow.id == deadline_id)
        )
        row = result.scalar_one_or_none()

        if row is None:
            return None

        return self._to_deadline(row)

    async def update_deadline(self, *, deadline: Deadline) -> None:
        await self._session.execute(
            update_sql(DeadlineRow)
            .where(DeadlineRow.id == deadline.id)
            .values(
                user_id=deadline.user_id,
                due_at=deadline.due_at,
                title=deadline.title,
                description=deadline.description,
                course_id=deadline.course_id,
                course_task_id=deadline.course_task_id,
                status=deadline.status.value,
            )
        )

    @staticmethod
    def _to_reminder(row: ReminderRow) -> Reminder:
        return Reminder(
            id=row.id,
            user_id=row.user_id,
            remind_at=row.remind_at,
            title=row.title,
            description=row.description,
            status=CommitmentStatus(row.status),
        )

    @staticmethod
    def _to_deadline(row: DeadlineRow) -> Deadline:
        return Deadline(
            id=row.id,
            user_id=row.user_id,
            due_at=row.due_at,
            title=row.title,
            description=row.description,
            course_id=row.course_id,
            course_task_id=row.course_task_id,
            status=CommitmentStatus(row.status),
        )

    @staticmethod
    def _to_reminder_row(reminder: Reminder) -> ReminderRow:
        return ReminderRow(
            id=reminder.id,
            user_id=reminder.user_id,
            remind_at=reminder.remind_at,
            title=reminder.title,
            description=reminder.description,
            status=reminder.status.value,
        )

    @staticmethod
    def _to_deadline_row(deadline: Deadline) -> DeadlineRow:
        return DeadlineRow(
            id=deadline.id,
            user_id=deadline.user_id,
            due_at=deadline.due_at,
            title=deadline.title,
            description=deadline.description,
            course_id=deadline.course_id,
            course_task_id=deadline.course_task_id,
            status=deadline.status.value,
        )
