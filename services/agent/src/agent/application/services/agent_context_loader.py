from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from uuid import UUID

from agent.application.dto.agent_context import AgentPlannerContextDto
from agent.application.dto.schedule import DeadlineDto, ReminderDto
from agent.application.ports.analytics_context import AnalyticsContextPort
from agent.application.ports.course_context import CourseContextPort
from agent.application.ports.schedule_context import ScheduleContextPort
from agent.application.ports.user_context import UserContextPort


@dataclass(frozen=True, slots=True)
class AgentContextLoader:
    user_context: UserContextPort
    course_context: CourseContextPort
    schedule_context: ScheduleContextPort
    analytics_context: AnalyticsContextPort

    async def load(
        self,
        user_id: UUID,
        *,
        today: date | None = None,
    ) -> AgentPlannerContextDto:
        resolved_today = today or date.today()
        tomorrow = resolved_today + timedelta(days=1)

        user_profile = await self.user_context.get_user_profile(user_id)

        analytics_observations = await self.analytics_context.list_observations(
            user_id,
            limit=20,
        )

        courses = await self.course_context.list_courses(user_id)

        commitments = await self.schedule_context.list_commitments(user_id)

        reminders: list[ReminderDto] = []
        deadlines: list[DeadlineDto] = []

        for commitment in commitments:
            if isinstance(commitment, ReminderDto):
                reminders.append(commitment)
            elif isinstance(commitment, DeadlineDto):
                deadlines.append(commitment)

        today_date_observations = await self.schedule_context.list_schedule_date_observations(
            user_id,
            date_=resolved_today,
        )
        tomorrow_date_observations = await self.schedule_context.list_schedule_date_observations(
            user_id,
            date_=tomorrow,
        )

        return AgentPlannerContextDto(
            user_id=user_id,
            today=resolved_today,
            user_profile=user_profile,
            analytics_observations=tuple(analytics_observations),
            courses=tuple(courses),
            reminders=tuple(reminders),
            deadlines=tuple(deadlines),
            date_observations=tuple(today_date_observations)
            + tuple(tomorrow_date_observations),
        )