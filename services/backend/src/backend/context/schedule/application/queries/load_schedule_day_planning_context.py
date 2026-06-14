from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from direttore import AbstractQueryHandler, Query

from backend.context.schedule.application.orchestration import (
    ScheduleQueryHandlerContext,
    query_handler_registry,
)
from backend.context.schedule.application.ports.analytics_planning_context_port import (
    AnalyticsPlanningContextPort,
    AnalyticsPlanningInsightReadModel,
)
from backend.context.schedule.application.ports.course_planning_context_port import (
    CoursePlanningContextPort,
)
from backend.context.schedule.domain.commitment.entities.deadline import Deadline
from backend.context.schedule.domain.commitment.value_objects.commitment_status import (
    CommitmentStatus,
)
from backend.context.schedule.domain.execution.entities.schedule_date_observation import (
    ScheduleDateObservation,
)
from backend.context.schedule.domain.execution.entities.schedule_day import ScheduleDay
from backend.context.schedule.domain.execution.entities.schedule_day_observation import (
    ScheduleDayObservation,
)
from backend.context.schedule.domain.execution.entities.scheduled_activity import (
    ScheduledActivity,
)
from backend.context.schedule.domain.shared.local_time import LocalTime
from backend.context.schedule.domain.shared.schedule_date import ScheduleDate
from backend.context.schedule.domain.shared.time_block_kind import TimeBlockKind
from backend.context.schedule.domain.template.entities.schedule_day_template import (
    ScheduleDayTemplate,
)
from backend.context.schedule.domain.template.entities.time_block import TimeBlock
from backend.context.schedule.domain.template.entities.weekly_schedule_observation import (
    WeeklyScheduleObservation,
)
from backend.context.schedule.domain.template.value_objects.weekday import Weekday


@dataclass(frozen=True, kw_only=True)
class PlanningTemplateTimeBlockReadModel:
    id: UUID
    start_time: LocalTime
    end_time: LocalTime
    kind: TimeBlockKind
    title: str
    description: str | None


@dataclass(frozen=True, kw_only=True)
class PlanningTemplateReadModel:
    weekday: Weekday
    time_blocks: list[PlanningTemplateTimeBlockReadModel]
    observations: list[str]


@dataclass(frozen=True, kw_only=True)
class PlanningDeadlineReadModel:
    id: UUID
    due_at: object
    title: str
    description: str | None


@dataclass(frozen=True, kw_only=True)
class PlanningDateObservationReadModel:
    id: UUID
    starts_on: ScheduleDate
    ends_on: ScheduleDate | None
    description: str


@dataclass(frozen=True, kw_only=True)
class RecentPlannedActivityContextReadModel:
    title: str
    course_task_id: UUID | None
    course_task_status: str | None


@dataclass(frozen=True, kw_only=True)
class RecentScheduleDayContextReadModel:
    date: ScheduleDate
    title: str
    description: str
    observations: list[str]
    planned_activities: list[RecentPlannedActivityContextReadModel]


@dataclass(frozen=True, kw_only=True)
class PlanningAnalyticsInsightReadModel:
    description: str


@dataclass(frozen=True, kw_only=True)
class LoadScheduleDayPlanningContextQuery(Query):
    user_id: UUID
    target_date: ScheduleDate
    previous_days_limit: int = 2
    include_weekly_observations: bool = True


@dataclass(frozen=True, kw_only=True)
class LoadScheduleDayPlanningContextQueryResult:
    user_id: UUID
    target_date: ScheduleDate
    weekday: Weekday
    template: PlanningTemplateReadModel
    active_deadlines: list[PlanningDeadlineReadModel]
    date_observations: list[PlanningDateObservationReadModel]
    recent_days: list[RecentScheduleDayContextReadModel]
    analytics_insights: list[PlanningAnalyticsInsightReadModel]


@query_handler_registry.handler(LoadScheduleDayPlanningContextQuery)
class LoadScheduleDayPlanningContextQueryHandler(AbstractQueryHandler):

    def __init__(self, course_planning_context: CoursePlanningContextPort, analytics_planning_context: AnalyticsPlanningContextPort):
        self.course_planning_context = course_planning_context
        self.analytics_planning_context = analytics_planning_context

    async def __call__(
        self,
        query: LoadScheduleDayPlanningContextQuery,
        context: ScheduleQueryHandlerContext,
    ) -> LoadScheduleDayPlanningContextQueryResult:
        if query.previous_days_limit < 0:
            raise ValueError("previous_days_limit cannot be negative")

        template = (
            await context.uow.template_reader.get_weekly_schedule_template_by_user_id(
                user_id=query.user_id,
            )
        )

        if template is None:
            raise ValueError("weekly schedule template not found")

        weekday = self._weekday_from_date(query.target_date)
        day_template = template.get_day(weekday)

        active_deadlines = await context.uow.commitment_reader.list_deadlines(
            user_id=query.user_id,
            status=CommitmentStatus.ACTIVE,
        )

        date_observations = await context.uow.execution_reader.list_schedule_date_observations(
            user_id=query.user_id,
            date=query.target_date,
        )

        recent_schedule_days = await self._load_recent_schedule_days(
            user_id=query.user_id,
            target_date=query.target_date,
            previous_days_limit=query.previous_days_limit,
            context=context,
        )

        course_task_ids = self._collect_course_task_ids(recent_schedule_days)

        course_context = (
            await self.course_planning_context.get_recent_planned_course_activity_context(
                user_id=query.user_id,
                course_task_ids=course_task_ids,
            )
        )

        course_task_status_by_id = {
            item.course_task_id: item.course_task_status
            for item in course_context.recent_activities
            if item.course_task_id is not None
        }

        analytics_context = await self.analytics_planning_context.get_user_planning_context(
            user_id=query.user_id,
        )

        return LoadScheduleDayPlanningContextQueryResult(
            user_id=query.user_id,
            target_date=query.target_date,
            weekday=weekday,
            template=self._map_template(
                day_template=day_template,
                weekly_observations=template.observations,
                include_weekly_observations=query.include_weekly_observations,
            ),
            active_deadlines=[
                self._map_deadline(deadline)
                for deadline in active_deadlines
            ],
            date_observations=[
                self._map_date_observation(observation)
                for observation in date_observations
            ],
            recent_days=[
                self._map_recent_schedule_day(
                    schedule_day=schedule_day,
                    course_task_status_by_id=course_task_status_by_id,
                )
                for schedule_day in recent_schedule_days
            ],
            analytics_insights=[
                self._map_analytics_insight(insight)
                for insight in analytics_context.insights
            ],
        )

    @staticmethod
    def _weekday_from_date(date: ScheduleDate) -> Weekday:
        return Weekday.all()[date.to_date().weekday()]

    async def _load_recent_schedule_days(
        self,
        *,
        user_id: UUID,
        target_date: ScheduleDate,
        previous_days_limit: int,
        context: ScheduleQueryHandlerContext,
    ) -> list[ScheduleDay]:
        recent_days: list[ScheduleDay] = []

        target_python_date = target_date.to_date()

        for offset in range(1, previous_days_limit + 1):
            previous_python_date = target_python_date - __import__(
                "datetime"
            ).timedelta(days=offset)

            previous_schedule_date = ScheduleDate(
                year=previous_python_date.year,
                month=previous_python_date.month,
                day=previous_python_date.day,
            )

            schedule_day = (
                await context.uow.execution_reader.get_schedule_day_by_user_id_and_date(
                    user_id=user_id,
                    date=previous_schedule_date,
                )
            )

            if schedule_day is not None:
                recent_days.append(schedule_day)

        return recent_days

    @staticmethod
    def _collect_course_task_ids(schedule_days: list[ScheduleDay]) -> list[UUID]:
        course_task_ids: list[UUID] = []

        for schedule_day in schedule_days:
            for activity in schedule_day.activities:
                if activity.course_task_id is None:
                    continue

                if activity.course_task_id not in course_task_ids:
                    course_task_ids.append(activity.course_task_id)

        return course_task_ids

    @classmethod
    def _map_template(
        cls,
        *,
        day_template: ScheduleDayTemplate,
        weekly_observations: list[WeeklyScheduleObservation],
        include_weekly_observations: bool,
    ) -> PlanningTemplateReadModel:
        return PlanningTemplateReadModel(
            weekday=day_template.weekday,
            time_blocks=[
                cls._map_template_time_block(block)
                for block in day_template.time_blocks
            ],
            observations=[
                observation.description
                for observation in weekly_observations
            ]
            if include_weekly_observations
            else [],
        )

    @staticmethod
    def _map_template_time_block(
        block: TimeBlock,
    ) -> PlanningTemplateTimeBlockReadModel:
        return PlanningTemplateTimeBlockReadModel(
            id=block.id,
            start_time=block.start_time,
            end_time=block.end_time,
            kind=block.kind,
            title=block.title,
            description=block.description,
        )

    @staticmethod
    def _map_deadline(deadline: Deadline) -> PlanningDeadlineReadModel:
        return PlanningDeadlineReadModel(
            id=deadline.id,
            due_at=deadline.due_at,
            title=deadline.title,
            description=deadline.description,
        )

    @staticmethod
    def _map_date_observation(
        observation: ScheduleDateObservation,
    ) -> PlanningDateObservationReadModel:
        return PlanningDateObservationReadModel(
            id=observation.id,
            starts_on=observation.starts_on,
            ends_on=observation.ends_on,
            description=observation.description,
        )

    @classmethod
    def _map_recent_schedule_day(
        cls,
        *,
        schedule_day: ScheduleDay,
        course_task_status_by_id: dict[UUID, str | None],
    ) -> RecentScheduleDayContextReadModel:
        return RecentScheduleDayContextReadModel(
            date=schedule_day.date,
            title=schedule_day.title,
            description=schedule_day.description,
            observations=[
                cls._map_schedule_day_observation(observation)
                for observation in schedule_day.observations
            ],
            planned_activities=[
                cls._map_recent_planned_activity(
                    activity=activity,
                    course_task_status_by_id=course_task_status_by_id,
                )
                for activity in schedule_day.activities
            ],
        )

    @staticmethod
    def _map_schedule_day_observation(
        observation: ScheduleDayObservation,
    ) -> str:
        return observation.description

    @staticmethod
    def _map_recent_planned_activity(
        *,
        activity: ScheduledActivity,
        course_task_status_by_id: dict[UUID, str | None],
    ) -> RecentPlannedActivityContextReadModel:
        return RecentPlannedActivityContextReadModel(
            title=activity.title,
            course_task_id=activity.course_task_id,
            course_task_status=course_task_status_by_id.get(activity.course_task_id)
            if activity.course_task_id is not None
            else None,
        )

    @staticmethod
    def _map_analytics_insight(
        insight: AnalyticsPlanningInsightReadModel,
    ) -> PlanningAnalyticsInsightReadModel:
        return PlanningAnalyticsInsightReadModel(
            description=insight.description,
        )