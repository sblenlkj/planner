from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from direttore import AbstractCommandHandler, Command

from backend.context.schedule.application.orchestration import (
    ScheduleCommandHandlerContext,
    command_handler_registry,
)
from backend.context.schedule.domain.commitment.entities.deadline import Deadline


@dataclass(frozen=True, kw_only=True)
class CreateDeadlineCommand(Command):
    user_id: UUID
    due_at: datetime
    title: str
    description: str | None = None
    id: UUID | None = None


@dataclass(frozen=True, kw_only=True)
class CreateDeadlineCommandResult:
    deadline_id: UUID


@command_handler_registry.handler(CreateDeadlineCommand)
class CreateDeadlineCommandHandler(AbstractCommandHandler):
    async def __call__(
        self,
        command: CreateDeadlineCommand,
        context: ScheduleCommandHandlerContext,
    ) -> CreateDeadlineCommandResult:
        deadline_id = command.id or uuid4()

        deadline = Deadline(
            id=deadline_id,
            user_id=command.user_id,
            due_at=self._to_utc(local_datetime=command.due_at),
            title=command.title,
            description=command.description,
            course_id=None,
            course_task_id=None,
        )

        await context.uow.commitment_writer.add_deadline(
            deadline=deadline,
        )

        return CreateDeadlineCommandResult(
            deadline_id=deadline_id,
        )
    
    @staticmethod
    def _to_utc(
        *,
        local_datetime: datetime,
    ) -> datetime:
        # Contract:
        # utc_offset_minutes is the user's standard offset from UTC.
        #
        # Examples:
        # UTC+3  -> +180
        # UTC-5  -> -300
        #
        # Conversion:
        # local time -> UTC time
        # UTC = local - offset
        #
        # Example:
        # local_datetime=2026-06-16 09:30:00
        # utc_offset_minutes=180
        # stored UTC=2026-06-16 06:30:00
        #
        # Database stores UTC as TIMESTAMP WITHOUT TIME ZONE.
        # If datetime has tzinfo, ignore tzinfo and treat wall time as user-local.

        local_naive = local_datetime.replace(tzinfo=None)

        return local_naive