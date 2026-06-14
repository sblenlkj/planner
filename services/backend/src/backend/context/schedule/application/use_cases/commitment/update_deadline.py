from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from direttore import AbstractCommandHandler, Command

from backend.context.schedule.application.orchestration import (
    ScheduleCommandHandlerContext,
    command_handler_registry,
)
from backend.context.schedule.domain.commitment.value_objects.commitment_status import (
    CommitmentStatus,
)


@dataclass(frozen=True, kw_only=True)
class UpdateDeadlineCommand(Command):
    deadline_id: UUID
    due_at: datetime | None = None
    title: str | None = None
    description: str | None = None
    status: CommitmentStatus | None = None


@dataclass(frozen=True, kw_only=True)
class UpdateDeadlineCommandResult:
    deadline_id: UUID


@command_handler_registry.handler(UpdateDeadlineCommand)
class UpdateDeadlineCommandHandler(AbstractCommandHandler):
    async def __call__(
        self,
        command: UpdateDeadlineCommand,
        context: ScheduleCommandHandlerContext,
    ) -> UpdateDeadlineCommandResult:
        deadline = await context.uow.commitment_writer.get_deadline_by_id(
            deadline_id=command.deadline_id,
        )

        if deadline is None:
            raise ValueError("deadline not found")

        if command.due_at is not None:
            deadline.reschedule(command.due_at)

        if command.title is not None:
            deadline.rename(command.title)

        if command.description is not None:
            deadline.change_description(command.description)

        if command.status is not None:
            if command.status == CommitmentStatus.ACTIVE:
                deadline.reactivate()
            elif command.status == CommitmentStatus.CANCELLED:
                deadline.cancel()
            else:
                raise ValueError("unsupported deadline status")

        await context.uow.commitment_writer.update_deadline(
            deadline=deadline,
        )

        return UpdateDeadlineCommandResult(
            deadline_id=deadline.id,
        )