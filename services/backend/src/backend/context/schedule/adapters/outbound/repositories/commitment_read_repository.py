from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.context.schedule.adapters.outbound.models import DeadlineRow, ReminderRow
from backend.context.schedule.application.ports.repositories.commitment_read_repository import (
    CommitmentReadRepository,
)
from backend.context.schedule.domain.commitment.entities.deadline import Deadline
from backend.context.schedule.domain.commitment.entities.reminder import Reminder
from backend.context.schedule.domain.commitment.value_objects.commitment_status import (
    CommitmentStatus,
)


class SqlAlchemyCommitmentReadRepository(CommitmentReadRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_reminder_by_id(self, reminder_id: UUID) -> Reminder | None:
        result = await self._session.execute(
            select(ReminderRow).where(ReminderRow.id == reminder_id)
        )
        row = result.scalar_one_or_none()

        if row is None:
            return None

        return self._to_reminder(row)

    async def get_deadline_by_id(self, deadline_id: UUID) -> Deadline | None:
        result = await self._session.execute(
            select(DeadlineRow).where(DeadlineRow.id == deadline_id)
        )
        row = result.scalar_one_or_none()

        if row is None:
            return None

        return self._to_deadline(row)

    async def list_reminders(
        self,
        user_id: UUID,
        status: CommitmentStatus | None = None,
    ) -> list[Reminder]:
        statement = select(ReminderRow).where(ReminderRow.user_id == user_id)

        if status is not None:
            statement = statement.where(ReminderRow.status == status.value)

        statement = statement.order_by(ReminderRow.remind_at)

        result = await self._session.execute(statement)
        rows = result.scalars().all()

        return [self._to_reminder(row) for row in rows]

    async def list_deadlines(
        self,
        user_id: UUID,
        status: CommitmentStatus | None = None,
    ) -> list[Deadline]:
        statement = select(DeadlineRow).where(DeadlineRow.user_id == user_id)

        if status is not None:
            statement = statement.where(DeadlineRow.status == status.value)

        statement = statement.order_by(DeadlineRow.due_at)

        result = await self._session.execute(statement)
        rows = result.scalars().all()

        return [self._to_deadline(row) for row in rows]

    async def list_active_future_reminders(
        self,
        now_utc: datetime,
    ) -> list[Reminder]:
        statement = (
            select(ReminderRow)
            .where(ReminderRow.status == CommitmentStatus.ACTIVE.value)
            .where(ReminderRow.remind_at >= now_utc)
            .order_by(ReminderRow.remind_at)
        )

        result = await self._session.execute(statement)
        rows = result.scalars().all()

        return [self._to_reminder(row) for row in rows]

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