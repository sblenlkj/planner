from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from direttore import AbstractQueryHandler, Query

from backend.context.schedule.application.orchestration import (
    ScheduleQueryHandlerContext,
    query_handler_registry,
)
from backend.context.schedule.domain.execution.entities.schedule_day import ScheduleDay
from backend.context.schedule.domain.execution.entities.schedule_day_observation import (
    ScheduleDayObservation,
)
from backend.context.schedule.domain.execution.entities.scheduled_activity import (
    ScheduledActivity,
)
from backend.context.schedule.domain.execution.entities.scheduled_block import (
    ScheduledBlock,
)
from backend.context.schedule.domain.shared.local_time import LocalTime
from backend.context.schedule.domain.shared.schedule_date import ScheduleDate
from backend.context.schedule.domain.shared.time_block_kind import TimeBlockKind


@dataclass(frozen=True, kw_only=True)
class ScheduledBlockReadModel:
    id: UUID
    start_time: LocalTime
    end_time: LocalTime
    kind: TimeBlockKind
    title: str
    description: str | None


@dataclass(frozen=True, kw_only=True)
class ScheduledActivityReadModel:
    id: UUID
    start_time: LocalTime
    end_time: LocalTime
    title: str
    description: str | None
    course_task_id: UUID | None


@dataclass(frozen=True, kw_only=True)
class ScheduleDayObservationReadModel:
    id: UUID
    description: str


@dataclass(frozen=True, kw_only=True)
class ScheduleDayReadModel:
    user_id: UUID
    date: ScheduleDate
    title: str
    description: str
    blocks: list[ScheduledBlockReadModel]
    activities: list[ScheduledActivityReadModel]
    observations: list[ScheduleDayObservationReadModel]


@dataclass(frozen=True, kw_only=True)
class GetScheduleDayQuery(Query):
    user_id: UUID
    date: ScheduleDate
    include_observations: bool = False


@dataclass(frozen=True, kw_only=True)
class GetScheduleDayQueryResult:
    schedule_day: ScheduleDayReadModel | None


@query_handler_registry.handler(GetScheduleDayQuery)
class GetScheduleDayQueryHandler(AbstractQueryHandler):
    async def __call__(
        self,
        query: GetScheduleDayQuery,
        context: ScheduleQueryHandlerContext,
    ) -> GetScheduleDayQueryResult:
        schedule_day = (
            await context.uow.execution_reader.get_schedule_day_by_user_id_and_date(
                user_id=query.user_id,
                date=query.date,
            )
        )

        if schedule_day is None:
            return GetScheduleDayQueryResult(
                schedule_day=None,
            )

        return GetScheduleDayQueryResult(
            schedule_day=self._map_schedule_day(
                schedule_day=schedule_day,
                include_observations=query.include_observations,
            ),
        )

    @classmethod
    def _map_schedule_day(
        cls,
        *,
        schedule_day: ScheduleDay,
        include_observations: bool,
    ) -> ScheduleDayReadModel:
        return ScheduleDayReadModel(
            user_id=schedule_day.user_id,
            date=schedule_day.date,
            title=schedule_day.title,
            description=schedule_day.description,
            blocks=[
                cls._map_block(block)
                for block in schedule_day.blocks
            ],
            activities=[
                cls._map_activity(activity)
                for activity in schedule_day.activities
            ],
            observations=[
                cls._map_observation(observation)
                for observation in schedule_day.observations
            ]
            if include_observations
            else [],
        )

    @staticmethod
    def _map_block(block: ScheduledBlock) -> ScheduledBlockReadModel:
        return ScheduledBlockReadModel(
            id=block.id,
            start_time=block.start_time,
            end_time=block.end_time,
            kind=block.kind,
            title=block.title,
            description=block.description,
        )

    @staticmethod
    def _map_activity(activity: ScheduledActivity) -> ScheduledActivityReadModel:
        return ScheduledActivityReadModel(
            id=activity.id,
            start_time=activity.start_time,
            end_time=activity.end_time,
            title=activity.title,
            description=activity.description,
            course_task_id=activity.course_task_id,
        )

    @staticmethod
    def _map_observation(
        observation: ScheduleDayObservation,
    ) -> ScheduleDayObservationReadModel:
        return ScheduleDayObservationReadModel(
            id=observation.id,
            description=observation.description,
        )