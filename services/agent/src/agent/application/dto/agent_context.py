from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from agent.application.dto.analytics import AnalyticsObservationDto
from agent.application.dto.course import CourseDto
from agent.application.dto.schedule import (
    DeadlineDto,
    ReminderDto,
    ScheduleDateObservationDto,
)
from agent.application.dto.user import UserProfileDto


@dataclass(frozen=True, slots=True)
class AgentPlannerContextDto:
    user_id: UUID
    today: date
    user_profile: UserProfileDto
    analytics_observations: tuple[AnalyticsObservationDto, ...]
    courses: tuple[CourseDto, ...]
    reminders: tuple[ReminderDto, ...]
    deadlines: tuple[DeadlineDto, ...]
    date_observations: tuple[ScheduleDateObservationDto, ...]