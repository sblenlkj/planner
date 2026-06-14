from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any

from direttore import AbstractCommandHandler, Command

from backend.context.runtime.application.orchestration import (
    RuntimeCommandHandlerContext,
    command_handler_registry,
)
from backend.context.runtime.application.ports.schedule_runtime_port import (
    MorningDayMessageStatus,
    ScheduleRuntimePort,
)
from backend.context.runtime.application.ports.telegram_gateway_port import (
    TelegramGatewayPort,
)
from backend.context.runtime.application.ports.user_runtime_port import (
    UserRuntimePort,
)
from backend.context.runtime.application.runtime_jobs import (
    MORNING_DELIVERY_HANDLER_KEY,
    MORNING_DELIVERY_JOB_KEY,
)
from backend.context.runtime.domain.models import (
    RuntimeJobExecution,
    RuntimeJobExecutionSource,
    RuntimeJobExecutionStatus,
)


ROLLING_WINDOW_HOURS = 24


@dataclass(frozen=True, kw_only=True)
class SendMorningDayMessagesCommand(Command):
    source: RuntimeJobExecutionSource = RuntimeJobExecutionSource.CRON
    force: bool = False
    now_utc: datetime | None = None
    target_day: date | None = None


@dataclass(frozen=True, kw_only=True)
class SendMorningDayMessagesCommandResult:
    status: RuntimeJobExecutionStatus
    processed_count: int
    delivered_count: int
    skipped_count: int
    failed_count: int


@command_handler_registry.handler(
    SendMorningDayMessagesCommand,
    key=MORNING_DELIVERY_HANDLER_KEY,
)
class SendMorningDayMessagesCommandHandler(AbstractCommandHandler):
    def __init__(
        self,
        *,
        user_runtime_port: UserRuntimePort,
        schedule_runtime_port: ScheduleRuntimePort,
        telegram_gateway_port: TelegramGatewayPort,
    ) -> None:
        self._user_runtime_port = user_runtime_port
        self._schedule_runtime_port = schedule_runtime_port
        self._telegram_gateway_port = telegram_gateway_port

    async def __call__(
        self,
        command: SendMorningDayMessagesCommand,
        context: RuntimeCommandHandlerContext,
    ) -> SendMorningDayMessagesCommandResult:
        now_utc = self._resolve_now_utc(command.now_utc)
        window_start = self._rolling_window_start_utc(now_utc)
        target_day = command.target_day or now_utc.date()

        job = await context.uow.runtime_repository.get_job_by_key(
            MORNING_DELIVERY_JOB_KEY,
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

            return SendMorningDayMessagesCommandResult(
                status=execution.status,
                processed_count=0,
                delivered_count=0,
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

            return SendMorningDayMessagesCommandResult(
                status=execution.status,
                processed_count=0,
                delivered_count=0,
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

        delivered_user_ids: list[str] = []
        skipped_users: list[dict[str, str]] = []
        failed_users: list[dict[str, str]] = []

        for user_id in user_ids:
            try:
                message_result = await self._schedule_runtime_port.build_morning_day_message(
                    user_id=user_id,
                    day=target_day,
                )
            except Exception as exc:
                failed_users.append(
                    {
                        "user_id": str(user_id),
                        "stage": "build_morning_day_message",
                        "error": str(exc),
                    }
                )
                continue

            if message_result.status == MorningDayMessageStatus.NOT_READY:
                skipped_users.append(
                    {
                        "user_id": str(user_id),
                        "reason": message_result.reason or "day_not_ready",
                    }
                )
                continue

            if message_result.status == MorningDayMessageStatus.ERROR:
                failed_users.append(
                    {
                        "user_id": str(user_id),
                        "stage": "build_morning_day_message",
                        "error": message_result.reason or "unknown_schedule_error",
                    }
                )
                continue

            if not message_result.text or not message_result.text.strip():
                skipped_users.append(
                    {
                        "user_id": str(user_id),
                        "reason": "empty_morning_message",
                    }
                )
                continue

            try:
                await self._telegram_gateway_port.send_message(
                    user_id=user_id,
                    text=message_result.text,
                )
            except Exception as exc:
                failed_users.append(
                    {
                        "user_id": str(user_id),
                        "stage": "send_telegram_message",
                        "error": str(exc),
                    }
                )
                continue

            delivered_user_ids.append(str(user_id))

        finished_at = datetime.now(UTC)

        metadata: dict[str, Any] = {
            "window_start": window_start.isoformat(),
            "window_hours": ROLLING_WINDOW_HOURS,
            "target_day": target_day.isoformat(),
            "processed_count": len(user_ids),
            "delivered_count": len(delivered_user_ids),
            "skipped_count": len(skipped_users),
            "failed_count": len(failed_users),
            "delivered_user_ids": delivered_user_ids,
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

        return SendMorningDayMessagesCommandResult(
            status=status,
            processed_count=len(user_ids),
            delivered_count=len(delivered_user_ids),
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