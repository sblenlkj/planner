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
            due_at=command.due_at,
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