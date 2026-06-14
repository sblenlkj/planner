from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any
from uuid import UUID

from direttore import AbstractCommandHandler, Command

from backend.context.runtime.application.orchestration import (
    RuntimeCommandHandlerContext,
    command_handler_registry,
)
from backend.context.runtime.application.runtime_jobs import (
    BATCH_OBSERVATIONS_HANDLER_KEY, BATCH_OBSERVATIONS_JOB_KEY
)
from backend.context.runtime.application.ports.observation_stream_port import (
    ExtractedObservationReadModel,
    ObservationBatchToPublish,
    ObservationStreamPort,
)
from backend.context.runtime.domain.models import (
    RuntimeJobExecution,
    RuntimeJobExecutionSource,
    RuntimeJobExecutionStatus,
)

DEFAULT_READ_LIMIT = 1000
ROLLING_WINDOW_HOURS = 24


@dataclass(frozen=True, kw_only=True)
class BatchExtractedObservationsCommand(Command):
    source: RuntimeJobExecutionSource = RuntimeJobExecutionSource.CRON
    force: bool = False
    now_utc: datetime | None = None
    read_limit: int = DEFAULT_READ_LIMIT


@dataclass(frozen=True, kw_only=True)
class BatchExtractedObservationsCommandResult:
    status: RuntimeJobExecutionStatus
    read_event_count: int
    published_batch_count: int
    user_count: int
    last_committed_stream_id: str | None


@command_handler_registry.handler(
    BatchExtractedObservationsCommand,
    key=BATCH_OBSERVATIONS_HANDLER_KEY,
)
class BatchExtractedObservationsCommandHandler(AbstractCommandHandler):
    def __init__(
        self,
        *,
        observation_stream_port: ObservationStreamPort,
    ) -> None:
        self._observation_stream_port = observation_stream_port

    async def __call__(
        self,
        command: BatchExtractedObservationsCommand,
        context: RuntimeCommandHandlerContext,
    ) -> BatchExtractedObservationsCommandResult:
        now_utc = self._resolve_now_utc(command.now_utc)
        window_start = self._rolling_window_start_utc(now_utc)

        job = await context.uow.runtime_repository.get_job_by_key(
            BATCH_OBSERVATIONS_JOB_KEY,
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

            return BatchExtractedObservationsCommandResult(
                status=execution.status,
                read_event_count=0,
                published_batch_count=0,
                user_count=0,
                last_committed_stream_id=None,
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

            return BatchExtractedObservationsCommandResult(
                status=execution.status,
                read_event_count=0,
                published_batch_count=0,
                user_count=0,
                last_committed_stream_id=None,
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
                    "read_limit": command.read_limit,
                },
            )

            job.mark_started(started_at=now_utc)

            await context.uow.runtime_repository.add_execution(execution)
            await context.uow.runtime_repository.update_job(job)

        messages = await self._observation_stream_port.read_new_extracted_observations(
            limit=command.read_limit,
        )

        batches = self._build_batches(
            messages=messages,
            batch_date=now_utc.date(),
        )

        published_stream_ids: list[str] = []
        failed_batches: list[dict[str, str]] = []

        for batch in batches:
            try:
                published = await self._observation_stream_port.publish_observation_batch(
                    batch,
                )
            except Exception as exc:
                failed_batches.append(
                    {
                        "business_user_id": str(batch.business_user_id),
                        "error": str(exc),
                    }
                )
                continue

            published_stream_ids.append(published.stream_id)

        last_committed_stream_id: str | None = None

        if messages and not failed_batches:
            last_committed_stream_id = messages[-1].stream_id

            await self._observation_stream_port.commit_read_offset(
                stream_id=last_committed_stream_id,
            )

        finished_at = datetime.now(UTC)

        metadata: dict[str, Any] = {
            "window_start": window_start.isoformat(),
            "window_hours": ROLLING_WINDOW_HOURS,
            "read_limit": command.read_limit,
            "read_event_count": len(messages),
            "published_batch_count": len(published_stream_ids),
            "user_count": len(batches),
            "published_stream_ids": published_stream_ids,
            "failed_batches": failed_batches,
            "last_read_stream_id": messages[-1].stream_id if messages else None,
            "last_committed_stream_id": last_committed_stream_id,
            "tracking_enabled": job is not None,
        }

        if failed_batches:
            status = RuntimeJobExecutionStatus.COMPLETED_WITH_WARNINGS
        else:
            status = RuntimeJobExecutionStatus.COMPLETED

        if execution is not None:
            if failed_batches:
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
            if not failed_batches:
                job.mark_succeeded(finished_at=finished_at)

            await context.uow.runtime_repository.update_job(job)

        return BatchExtractedObservationsCommandResult(
            status=status,
            read_event_count=len(messages),
            published_batch_count=len(published_stream_ids),
            user_count=len(batches),
            last_committed_stream_id=last_committed_stream_id,
        )

    @staticmethod
    def _build_batches(
        *,
        messages: tuple[ExtractedObservationReadModel, ...],
        batch_date: date,
    ) -> tuple[ObservationBatchToPublish, ...]:
        observations_by_user: dict[UUID, list[dict[str, str]]] = defaultdict(list)

        for message in messages:
            observations_by_user[message.business_user_id].extend(
                message.observations,
            )

        return tuple(
            ObservationBatchToPublish(
                business_user_id=business_user_id,
                batch_date=batch_date.isoformat(),
                observations=tuple(observations),
            )
            for business_user_id, observations in observations_by_user.items()
            if observations
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