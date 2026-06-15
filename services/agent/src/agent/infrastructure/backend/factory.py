from __future__ import annotations

from dataclasses import dataclass

from agent.application.ports import AnalyticsContextPort, CourseContextPort, ScheduleContextPort, UserContextPort
from agent.core.backend_settings import BackendApiSettings

from .analytics_context_adapter import HttpAnalyticsContextAdapter
from .course_context_adapter import HttpCourseContextAdapter
from .http_client import BackendHttpClient
from .schedule_context_adapter import HttpScheduleContextAdapter
from .user_context_adapter import HttpUserContextAdapter


@dataclass(frozen=True, slots=True)
class BackendContextAdapters:
    client: BackendHttpClient
    user: UserContextPort
    course: CourseContextPort
    schedule: ScheduleContextPort
    analytics: AnalyticsContextPort

    async def aclose(self) -> None:
        await self.client.aclose()


def build_backend_context_adapters(settings: BackendApiSettings | None = None) -> BackendContextAdapters:
    settings = settings or BackendApiSettings.from_env()
    client = BackendHttpClient(
        base_url=settings.base_url,
        timeout_seconds=settings.timeout_seconds,
        access_token=settings.access_token,
    )
    return BackendContextAdapters(
        client=client,
        user=HttpUserContextAdapter(client=client, settings=settings),
        course=HttpCourseContextAdapter(client=client, settings=settings),
        schedule=HttpScheduleContextAdapter(client=client, settings=settings),
        analytics=HttpAnalyticsContextAdapter(client=client, settings=settings),
    )
