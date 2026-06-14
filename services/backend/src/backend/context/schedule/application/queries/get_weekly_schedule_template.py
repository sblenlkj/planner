from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from direttore import AbstractQueryHandler, Query

from backend.context.schedule.application.orchestration import (
    ScheduleQueryHandlerContext,
    query_handler_registry,
)
from backend.context.schedule.domain.shared.local_time import LocalTime
from backend.context.schedule.domain.shared.time_block_kind import TimeBlockKind
from backend.context.schedule.domain.template.entities.schedule_day_template import (
    ScheduleDayTemplate,
)
from backend.context.schedule.domain.template.entities.time_block import TimeBlock
from backend.context.schedule.domain.template.entities.weekly_schedule_observation import (
    WeeklyScheduleObservation,
)
from backend.context.schedule.domain.template.entities.weekly_schedule_template import (
    WeeklyScheduleTemplate,
)
from backend.context.schedule.domain.template.value_objects.weekday import Weekday


@dataclass(frozen=True, kw_only=True)
class TemplateTimeBlockReadModel:
    id: UUID
    start_time: LocalTime
    end_time: LocalTime
    kind: TimeBlockKind
    title: str
    description: str | None


@dataclass(frozen=True, kw_only=True)
class TemplateDayReadModel:
    weekday: Weekday
    time_blocks: list[TemplateTimeBlockReadModel]


@dataclass(frozen=True, kw_only=True)
class WeeklyScheduleObservationReadModel:
    id: UUID
    description: str


@dataclass(frozen=True, kw_only=True)
class GetWeeklyScheduleTemplateQuery(Query):
    user_id: UUID
    weekday: Weekday | None = None
    include_observations: bool = False


@dataclass(frozen=True, kw_only=True)
class GetWeeklyScheduleTemplateQueryResult:
    template_id: UUID
    user_id: UUID
    days: list[TemplateDayReadModel]
    observations: list[WeeklyScheduleObservationReadModel]


@query_handler_registry.handler(GetWeeklyScheduleTemplateQuery)
class GetWeeklyScheduleTemplateQueryHandler(AbstractQueryHandler):
    async def __call__(
        self,
        query: GetWeeklyScheduleTemplateQuery,
        context: ScheduleQueryHandlerContext,
    ) -> GetWeeklyScheduleTemplateQueryResult:
        template = (
            await context.uow.template_reader.get_weekly_schedule_template_by_user_id(
                user_id=query.user_id,
            )
        )

        if template is None:
            raise ValueError("weekly schedule template not found")

        days = self._select_days(
            template=template,
            weekday=query.weekday,
        )

        observations = (
            [
                self._map_observation(observation)
                for observation in template.observations
            ]
            if query.include_observations
            else []
        )

        return GetWeeklyScheduleTemplateQueryResult(
            template_id=template.id,
            user_id=template.user_id,
            days=[self._map_day(day) for day in days],
            observations=observations,
        )

    @staticmethod
    def _select_days(
        *,
        template: WeeklyScheduleTemplate,
        weekday: Weekday | None,
    ) -> list[ScheduleDayTemplate]:
        if weekday is None:
            return template.days

        return [template.get_day(weekday)]

    @staticmethod
    def _map_day(day: ScheduleDayTemplate) -> TemplateDayReadModel:
        return TemplateDayReadModel(
            weekday=day.weekday,
            time_blocks=[
                GetWeeklyScheduleTemplateQueryHandler._map_time_block(block)
                for block in day.time_blocks
            ],
        )

    @staticmethod
    def _map_time_block(block: TimeBlock) -> TemplateTimeBlockReadModel:
        return TemplateTimeBlockReadModel(
            id=block.id,
            start_time=block.start_time,
            end_time=block.end_time,
            kind=block.kind,
            title=block.title,
            description=block.description,
        )

    @staticmethod
    def _map_observation(
        observation: WeeklyScheduleObservation,
    ) -> WeeklyScheduleObservationReadModel:
        return WeeklyScheduleObservationReadModel(
            id=observation.id,
            description=observation.description,
        )