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
from backend.context.schedule.domain.template.value_objects.weekday import Weekday


@dataclass(frozen=True, kw_only=True)
class ReplaceScheduleDayTemplateCommand(Command):
    user_id: UUID
    weekday: Weekday
    time_blocks: list[TimeBlockInput]


@dataclass(frozen=True, kw_only=True)
class ReplaceScheduleDayTemplateCommandResult:
    template_id: UUID
    weekday: Weekday


@command_handler_registry.handler(ReplaceScheduleDayTemplateCommand)
class ReplaceScheduleDayTemplateCommandHandler(AbstractCommandHandler):
    async def __call__(
        self,
        command: ReplaceScheduleDayTemplateCommand,
        context: ScheduleCommandHandlerContext,
    ) -> ReplaceScheduleDayTemplateCommandResult:
        template = await context.uow.template_writer.get_weekly_schedule_template_by_user_id(
            user_id=command.user_id,
        )

        if template is None:
            raise ValueError("weekly schedule template not found")

        day = ScheduleDayTemplate(
            weekly_schedule_template_id=template.id,
            weekday=command.weekday,
            time_blocks=[
                TimeBlock(
                    start_time=block.start_time,
                    end_time=block.end_time,
                    kind=block.kind,
                    title=block.title,
                    description=block.description,
                )
                for block in command.time_blocks
            ],
        )

        template.replace_day(day)

        await context.uow.template_writer.update_weekly_schedule_template(
            template=template,
        )

        return ReplaceScheduleDayTemplateCommandResult(
            template_id=template.id,
            weekday=command.weekday,
        )