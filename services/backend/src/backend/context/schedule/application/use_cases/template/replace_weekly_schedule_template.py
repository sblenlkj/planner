from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

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
class ReplaceScheduleDayTemplateInput:
    weekday: Weekday
    time_blocks: list[TimeBlockInput]


@dataclass(frozen=True, kw_only=True)
class ReplaceWeeklyScheduleTemplateCommand(Command):
    user_id: UUID
    days: list[ReplaceScheduleDayTemplateInput]


@dataclass(frozen=True, kw_only=True)
class ReplaceWeeklyScheduleTemplateCommandResult:
    template_id: UUID


@command_handler_registry.handler(ReplaceWeeklyScheduleTemplateCommand)
class ReplaceWeeklyScheduleTemplateCommandHandler(AbstractCommandHandler):
    async def __call__(
        self,
        command: ReplaceWeeklyScheduleTemplateCommand,
        context: ScheduleCommandHandlerContext,
    ) -> ReplaceWeeklyScheduleTemplateCommandResult:
        existing_template = (
            await context.uow.template_writer.get_weekly_schedule_template_by_user_id(
                user_id=command.user_id,
            )
        )

        if existing_template is None:
            raise ValueError("weekly schedule template not found")

        template = WeeklyScheduleTemplate(
            id=existing_template.id,
            user_id=existing_template.user_id,
            observations=existing_template.observations,
            days=[
                ScheduleDayTemplate(
                    weekly_schedule_template_id=existing_template.id,
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

        await context.uow.template_writer.update_weekly_schedule_template(
            template=template,
        )

        return ReplaceWeeklyScheduleTemplateCommandResult(
            template_id=template.id,
        )