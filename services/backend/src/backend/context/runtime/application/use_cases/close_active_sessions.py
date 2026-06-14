from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from direttore import AbstractCommandHandler, Command

from backend.context.runtime.application.orchestration import (
    RuntimeCommandHandlerContext,
    command_handler_registry,
)
from backend.context.runtime.application.runtime_jobs import (
    CLOSE_ACTIVE_SESSIONS_HANDLER_KEY, CLOSE_ACTIVE_SESSIONS_JOB_KEY
)
from backend.context.runtime.application.ports.telegram_gateway_port import (
    TelegramGatewayPort,
)
from backend.context.runtime.application.ports.user_runtime_port import (
    UserRuntimePort,
)
from backend.context.runtime.domain.models import (
    RuntimeJobExecution,
    RuntimeJobExecutionSource,
    RuntimeJobExecutionStatus,
)


@dataclass(frozen=True, kw_only=True)
class CloseActiveSessionsCommand(Command):
    source: RuntimeJobExecutionSource = RuntimeJobExecutionSource.CRON
    force: bool = False
    now_utc: datetime | None = None


@dataclass(frozen=True, kw_only=True)
class CloseActiveSessionsCommandResult:
    status: RuntimeJobExecutionStatus
    processed_count: int
    closed_count: int
    empty_count: int
    failed_count: int


@command_handler_registry.handler(
    CloseActiveSessionsCommand,
    key=CLOSE_ACTIVE_SESSIONS_HANDLER_KEY,
)
class CloseActiveSessionsCommandHandler(AbstractCommandHandler):
    def __init__(
        self,
        *,
        user_runtime_port: UserRuntimePort,
        telegram_gateway_port: TelegramGatewayPort,
    ) -> None:
        self._user_runtime_port = user_runtime_port
        self._telegram_gateway_port = telegram_gateway_port

    async def __call__(
        self,
        command: CloseActiveSessionsCommand,
        context: RuntimeCommandHandlerContext,
    ) -> CloseActiveSessionsCommandResult:
        now_utc = self._resolve_now_utc(command.now_utc)
        window_start = self._rolling_window_start_utc(now_utc)

        job = await context.uow.runtime_repository.get_job_by_key(
            CLOSE_ACTIVE_SESSIONS_JOB_KEY,
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

            return CloseActiveSessionsCommandResult(
                status=execution.status,
                processed_count=0,
                closed_count=0,
                empty_count=0,
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
                    "window_hours": 24,
                    "last_success_at": job.last_success_at.isoformat(),
                },
            )
            execution.skip(
                finished_at=now_utc,
                metadata={
                    "reason": "already_successfully_ran_in_rolling_window",
                    "window_hours": 24,
                },
            )

            await context.uow.runtime_repository.add_execution(execution)

            return CloseActiveSessionsCommandResult(
                status=execution.status,
                processed_count=0,
                closed_count=0,
                empty_count=0,
                failed_count=0,
            )

        execution: RuntimeJobExecution | None = None

        if job is not None:
            execution = RuntimeJobExecution.start(
                job_id=job.id,
                source=command.source,
                started_at=now_utc,
                metadata={"window_start": window_start.isoformat()},
            )

            job.mark_started(started_at=now_utc)

            await context.uow.runtime_repository.add_execution(execution)
            await context.uow.runtime_repository.update_job(job)

        user_ids = await self._user_runtime_port.get_ready_user_ids()

        closed_user_ids: list[str] = []
        empty_user_ids: list[str] = []
        failed_users: list[dict[str, str]] = []

        for user_id in user_ids:
            try:
                result = await self._telegram_gateway_port.close_conversation(
                    user_id=user_id,
                )
            except Exception as exc:
                failed_users.append(
                    {
                        "user_id": str(user_id),
                        "error": str(exc),
                    }
                )
                continue

            if result.closed:
                closed_user_ids.append(str(user_id))
            else:
                empty_user_ids.append(str(user_id))

        finished_at = datetime.now(UTC)

        metadata = {
            "window_start": window_start.isoformat(),
            "processed_count": len(user_ids),
            "closed_count": len(closed_user_ids),
            "empty_count": len(empty_user_ids),
            "failed_count": len(failed_users),
            "closed_user_ids": closed_user_ids,
            "empty_user_ids": empty_user_ids,
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

        return CloseActiveSessionsCommandResult(
            status=status,
            processed_count=len(user_ids),
            closed_count=len(closed_user_ids),
            empty_count=len(empty_user_ids),
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
        return now_utc - timedelta(hours=24)