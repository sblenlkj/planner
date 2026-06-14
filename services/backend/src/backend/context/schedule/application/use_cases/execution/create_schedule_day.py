from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from direttore import AbstractCommandHandler, Command

from backend.context.schedule.application.orchestration import (
    ScheduleCommandHandlerContext,
    command_handler_registry,
)
from backend.context.schedule.application.use_cases.execution.scheduled_activity_input import (
    ScheduledActivityInput,
)
from backend.context.schedule.domain.execution.entities.schedule_day import ScheduleDay
from backend.context.schedule.domain.execution.entities.scheduled_activity import (
    ScheduledActivity,
)
from backend.context.schedule.domain.execution.entities.scheduled_block import (
    ScheduledBlock,
)
from backend.context.schedule.domain.shared.schedule_date import ScheduleDate
from backend.context.schedule.domain.shared.time_block_kind import TimeBlockKind
from backend.context.schedule.domain.template.value_objects.weekday import Weekday


@dataclass(frozen=True, kw_only=True)
class CreateScheduleDayCommand(Command):
    user_id: UUID
    date: ScheduleDate
    title: str
    description: str
    activities: list[ScheduledActivityInput]


@dataclass(frozen=True, kw_only=True)
class CreateScheduleDayCommandResult:
    user_id: UUID
    date: ScheduleDate


@command_handler_registry.handler(CreateScheduleDayCommand)
class CreateScheduleDayCommandHandler(AbstractCommandHandler):
    async def __call__(
        self,
        command: CreateScheduleDayCommand,
        context: ScheduleCommandHandlerContext,
    ) -> CreateScheduleDayCommandResult:
        existing_day = (
            await context.uow.execution_writer.get_schedule_day_by_user_id_and_date(
                user_id=command.user_id,
                date=command.date,
            )
        )

        if existing_day is not None:
            raise ValueError("schedule day already exists")

        template = (
            await context.uow.template_writer.get_weekly_schedule_template_by_user_id(
                user_id=command.user_id,
            )
        )

        if template is None:
            raise ValueError("weekly schedule template not found")

        weekday = self._weekday_from_date(command.date)
        day_template = template.get_day(weekday)

        blocks = [
            ScheduledBlock(
                start_time=block.start_time,
                end_time=block.end_time,
                kind=block.kind,
                title=block.title,
                description=block.description,
            )
            for block in day_template.time_blocks
        ]

        schedule_day = ScheduleDay(
            user_id=command.user_id,
            date=command.date,
            title=command.title,
            description=command.description,
            blocks=blocks,
        )

        for activity_input in command.activities:
            activity = ScheduledActivity(
                start_time=activity_input.start_time,
                end_time=activity_input.end_time,
                title=activity_input.title,
                description=activity_input.description,
                course_task_id=activity_input.course_task_id,
            )

            self._validate_activity_fits_free_block(
                activity=activity,
                blocks=blocks,
            )

            schedule_day.add_activity(activity)

        await context.uow.execution_writer.add_schedule_day(
            schedule_day=schedule_day,
        )

        return CreateScheduleDayCommandResult(
            user_id=command.user_id,
            date=command.date,
        )

    @staticmethod
    def _weekday_from_date(date: ScheduleDate) -> Weekday:
        return Weekday.all()[date.to_date().weekday()]

    @staticmethod
    def _validate_activity_fits_free_block(
        *,
        activity: ScheduledActivity,
        blocks: list[ScheduledBlock],
    ) -> None:
        for block in blocks:
            if block.kind != TimeBlockKind.FREE:
                continue

            if (
                block.start_time <= activity.start_time
                and activity.end_time <= block.end_time
            ):
                return

        raise ValueError("scheduled activity must fit inside a FREE scheduled block")