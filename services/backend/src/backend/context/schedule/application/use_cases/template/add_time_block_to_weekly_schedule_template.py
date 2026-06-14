from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

from direttore import AbstractCommandHandler, Command

from backend.context.schedule.application.orchestration import (
    ScheduleCommandHandlerContext,
    command_handler_registry,
)
from backend.context.schedule.domain.shared.local_time import LocalTime
from backend.context.schedule.domain.shared.time_block_kind import TimeBlockKind
from backend.context.schedule.domain.template.entities.time_block import TimeBlock
from backend.context.schedule.domain.template.value_objects.weekday import Weekday


@dataclass(frozen=True, kw_only=True)
class AddTimeBlockToWeeklyScheduleTemplateCommand(Command):
    user_id: UUID
    weekdays: list[Weekday]
    start_time: LocalTime
    end_time: LocalTime
    kind: TimeBlockKind
    title: str
    description: str | None = None


@dataclass(frozen=True, kw_only=True)
class AddTimeBlockToWeeklyScheduleTemplateCommandResult:
    template_id: UUID
    time_block_ids: list[UUID]


@command_handler_registry.handler(AddTimeBlockToWeeklyScheduleTemplateCommand)
class AddTimeBlockToWeeklyScheduleTemplateCommandHandler(AbstractCommandHandler):
    async def __call__(
        self,
        command: AddTimeBlockToWeeklyScheduleTemplateCommand,
        context: ScheduleCommandHandlerContext,
    ) -> AddTimeBlockToWeeklyScheduleTemplateCommandResult:
        if not command.weekdays:
            raise ValueError("weekdays are required")

        template = await context.uow.template_writer.get_weekly_schedule_template_by_user_id(
            user_id=command.user_id,
        )

        if template is None:
            raise ValueError("weekly schedule template not found")

        time_block_ids: list[UUID] = []

        for weekday in command.weekdays:
            block_id = uuid4()

            day = template.get_day(weekday)
            day.add_time_block(
                TimeBlock(
                    id=block_id,
                    start_time=command.start_time,
                    end_time=command.end_time,
                    kind=command.kind,
                    title=command.title,
                    description=command.description,
                )
            )

            time_block_ids.append(block_id)

        await context.uow.template_writer.update_weekly_schedule_template(
            template=template,
        )

        return AddTimeBlockToWeeklyScheduleTemplateCommandResult(
            template_id=template.id,
            time_block_ids=time_block_ids,
        )