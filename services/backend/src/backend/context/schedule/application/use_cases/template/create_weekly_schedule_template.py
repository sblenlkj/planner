from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

from direttore import AbstractCommandHandler, Command

from backend.context.schedule.application.orchestration import (
    ScheduleCommandHandlerContext,
    command_handler_registry,
)
from backend.context.schedule.application.use_cases.template.time_block_input import (
    TimeBlockInput,
)
from backend.context.schedule.domain.template.entities.schedule_day_template import (
    ScheduleDayTemplate,
)
from backend.context.schedule.domain.template.entities.time_block import TimeBlock
from backend.context.schedule.domain.template.entities.weekly_schedule_template import (
    WeeklyScheduleTemplate,
)
from backend.context.schedule.domain.template.value_objects.weekday import Weekday


@dataclass(frozen=True, kw_only=True)
class CreateScheduleDayTemplateInput:
    weekday: Weekday
    time_blocks: list[TimeBlockInput]


@dataclass(frozen=True, kw_only=True)
class CreateWeeklyScheduleTemplateCommand(Command):
    user_id: UUID
    days: list[CreateScheduleDayTemplateInput]
    id: UUID | None = None


@dataclass(frozen=True, kw_only=True)
class CreateWeeklyScheduleTemplateCommandResult:
    template_id: UUID


@command_handler_registry.handler(CreateWeeklyScheduleTemplateCommand)
class CreateWeeklyScheduleTemplateCommandHandler(AbstractCommandHandler):
    async def __call__(
        self,
        command: CreateWeeklyScheduleTemplateCommand,
        context: ScheduleCommandHandlerContext,
    ) -> CreateWeeklyScheduleTemplateCommandResult:
        existing_template = (
            await context.uow.template_writer.get_weekly_schedule_template_by_user_id(
                user_id=command.user_id,
            )
        )

        if existing_template is not None:
            raise ValueError("weekly schedule template already exists")

        template_id = command.id or uuid4()

        template = WeeklyScheduleTemplate(
            id=template_id,
            user_id=command.user_id,
            days=[
                ScheduleDayTemplate(
                    weekly_schedule_template_id=template_id,
                    weekday=day.weekday,
                    time_blocks=[
                        TimeBlock(
                            start_time=block.start_time,
                            end_time=block.end_time,
                            kind=block.kind,
                            title=block.title,
                            description=block.description,
                        )
                        for block in day.time_blocks
                    ],
                )
                for day in command.days
            ],
        )

        await context.uow.template_writer.add_weekly_schedule_template(
            template=template,
        )

        return CreateWeeklyScheduleTemplateCommandResult(
            template_id=template.id,
        )