from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any
from uuid import UUID

from direttore import AbstractCommandHandler, Command

from backend.context.runtime.application.ports.user_runtime_port import (
    UserRuntimePort,
)
from backend.context.runtime.application.runtime_jobs import (
    GENERATE_DAY_HANDLER_KEY,
    GENERATE_DAY_JOB_KEY,
)
from backend.context.runtime.application.orchestration import (
    RuntimeCommandHandlerContext,
    command_handler_registry,
)
from backend.context.runtime.application.ports.day_generation_stream_port import (
    DayGenerationStreamPort,
)
from backend.context.runtime.application.ports.schedule_runtime_port import (
    ScheduleRuntimePort,
)
from backend.context.runtime.application.services.day_generation_request_service import (
    DayGenerationRequestService,
    DayGenerationRequestStatus,
)
from backend.context.runtime.domain.models import (
    RuntimeJobExecution,
    RuntimeJobExecutionSource,
    RuntimeJobExecutionStatus,
)


ROLLING_WINDOW_HOURS = 24


@dataclass(frozen=True, kw_only=True)
class RequestDayGenerationForReadyUsersCommand(Command):
    source: RuntimeJobExecutionSource = RuntimeJobExecutionSource.CRON
    force: bool = False
    now_utc: datetime | None = None
    target_day: date | None = None


@dataclass(frozen=True, kw_only=True)
class RequestDayGenerationForReadyUsersCommandResult:
    status: RuntimeJobExecutionStatus
    processed_count: int
    published_count: int
    skipped_count: int
    failed_count: int


@command_handler_registry.handler(
    RequestDayGenerationForReadyUsersCommand,
    key=GENERATE_DAY_HANDLER_KEY,
)
class RequestDayGenerationForReadyUsersCommandHandler(AbstractCommandHandler):
    def __init__(
        self,
        *,
        user_runtime_port: UserRuntimePort,
        schedule_runtime_port: ScheduleRuntimePort,
        day_generation_stream_port: DayGenerationStreamPort,
    ) -> None:
        self._user_runtime_port = user_runtime_port
        self._day_generation_request_service = DayGenerationRequestService(
            schedule_runtime_port=schedule_runtime_port,
            day_generation_stream_port=day_generation_stream_port,
        )

    async def __call__(
        self,
        command: RequestDayGenerationForReadyUsersCommand,
        context: RuntimeCommandHandlerContext,
    ) -> RequestDayGenerationForReadyUsersCommandResult:
        now_utc = self._resolve_now_utc(command.now_utc)
        window_start = self._rolling_window_start_utc(now_utc)
        target_day = command.target_day or now_utc.date()

        job = await context.uow.runtime_repository.get_job_by_key(
            GENERATE_DAY_JOB_KEY,
        )

        if job is not None and not job.is_enabled():
            execution = RuntimeJobExecution.start(
                job_id=job.id,
                source=command.source,
                started_at=now_utc,
                metadata={"reason": "job_disabled"},
            )
            execution.skip(
                finished_at=now_utc,
                metadata={"reason": "job_disabled"},
            )

            await context.uow.runtime_repository.add_execution(execution)

            return RequestDayGenerationForReadyUsersCommandResult(
                status=execution.status,
                processed_count=0,
                published_count=0,
                skipped_count=0,
                failed_count=0,
            )

        if (
            job is not None
            and not command.force
            and job.last_success_at is not None
            and job.last_success_at >= window_start
        ):
            execution = RuntimeJobExecution.start(
                job_id=job.id,
                source=command.source,
                started_at=now_utc,
                metadata={
                    "reason": "already_successfully_ran_in_rolling_window",
                    "window_start": window_start.isoformat(),
                    "window_hours": ROLLING_WINDOW_HOURS,
                    "last_success_at": job.last_success_at.isoformat(),
                },
            )
            execution.skip(
                finished_at=now_utc,
                metadata={
                    "reason": "already_successfully_ran_in_rolling_window",
                    "window_hours": ROLLING_WINDOW_HOURS,
                },
            )

            await context.uow.runtime_repository.add_execution(execution)

            return RequestDayGenerationForReadyUsersCommandResult(
                status=execution.status,
                processed_count=0,
                published_count=0,
                skipped_count=0,
                failed_count=0,
            )

        execution: RuntimeJobExecution | None = None

        if job is not None:
            execution = RuntimeJobExecution.start(
                job_id=job.id,
                source=command.source,
                started_at=now_utc,
                metadata={
                    "window_start": window_start.isoformat(),
                    "window_hours": ROLLING_WINDOW_HOURS,
                    "target_day": target_day.isoformat(),
                },
            )

            job.mark_started(started_at=now_utc)

            await context.uow.runtime_repository.add_execution(execution)
            await context.uow.runtime_repository.update_job(job)

        user_ids = await self._user_runtime_port.get_ready_user_ids()

        published_user_ids: list[str] = []
        skipped_users: list[dict[str, str]] = []
        failed_users: list[dict[str, str]] = []

        for user_id in user_ids:
            try:
                result = await self._day_generation_request_service.request_generation_if_missing(
                    user_id=user_id,
                    day=target_day,
                )
            except Exception as exc:
                failed_users.append(
                    {
                        "user_id": str(user_id),
                        "error": str(exc),
                    }
                )
                continue

            if result.status == DayGenerationRequestStatus.PUBLISHED:
                published_user_ids.append(str(user_id))
                continue

            if result.status == DayGenerationRequestStatus.SKIPPED_ALREADY_EXISTS:
                skipped_users.append(
                    {
                        "user_id": str(user_id),
                        "reason": result.status.value,
                    }
                )
                continue

        finished_at = datetime.now(UTC)

        metadata: dict[str, Any] = {
            "window_start": window_start.isoformat(),
            "window_hours": ROLLING_WINDOW_HOURS,
            "target_day": target_day.isoformat(),
            "processed_count": len(user_ids),
            "published_count": len(published_user_ids),
            "skipped_count": len(skipped_users),
            "failed_count": len(failed_users),
            "published_user_ids": published_user_ids,
            "skipped_users": skipped_users,
            "failed_users": failed_users,
            "tracking_enabled": job is not None,
        }

        if failed_users:
            status = RuntimeJobExecutionStatus.COMPLETED_WITH_WARNINGS
        else:
            status = RuntimeJobExecutionStatus.COMPLETED

        if execution is not None:
            if failed_users:
                execution.complete_with_warnings(
                    finished_at=finished_at,
                    metadata=metadata,
                )
            else:
                execution.complete(
                    finished_at=finished_at,
                    metadata=metadata,
                )

            await context.uow.runtime_repository.update_execution(execution)

        if job is not None:
            if not failed_users:
                job.mark_succeeded(finished_at=finished_at)

            await context.uow.runtime_repository.update_job(job)

        return RequestDayGenerationForReadyUsersCommandResult(
            status=status,
            processed_count=len(user_ids),
            published_count=len(published_user_ids),
            skipped_count=len(skipped_users),
            failed_count=len(failed_users),
        )

    @staticmethod
    def _resolve_now_utc(now_utc: datetime | None) -> datetime:
        if now_utc is None:
            return datetime.now(UTC)

        if now_utc.tzinfo is None:
            return now_utc.replace(tzinfo=UTC)

        return now_utc.astimezone(UTC)

    @staticmethod
    def _rolling_window_start_utc(now_utc: datetime) -> datetime:
        return now_utc - timedelta(hours=ROLLING_WINDOW_HOURS)