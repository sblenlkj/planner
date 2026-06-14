from __future__ import annotations

from dataclasses import dataclass

from direttore import AbstractCommandHandler, Command

from backend.shared.logging import get_logger

from backend.context.runtime.application.orchestration import (
    RuntimeCommandHandlerContext,
    command_handler_registry,
)
from backend.context.runtime.application.runtime_jobs import (
    ENSURE_RUNTIME_JOBS_HANDLER_KEY
)
from backend.context.runtime.application.runtime_jobs import (
    RUNTIME_JOB_DEFINITIONS,
)
from backend.context.runtime.domain.models import RuntimeJob
from backend.shared.application.ports.api_scheduler import (
    ApiScheduledCronOperation,
    ApiSchedulerPort,
)

logger = get_logger(__name__)

@dataclass(frozen=True, kw_only=True)
class EnsureRuntimeJobsCommand(Command):
    register_scheduler_jobs: bool = True


@dataclass(frozen=True, kw_only=True)
class EnsureRuntimeJobsCommandResult:
    created_count: int
    existing_count: int
    scheduled_count: int


@command_handler_registry.handler(EnsureRuntimeJobsCommand, key=ENSURE_RUNTIME_JOBS_HANDLER_KEY)
class EnsureRuntimeJobsCommandHandler(AbstractCommandHandler):
    def __init__(
        self,
        *,
        api_scheduler: ApiSchedulerPort,
    ) -> None:
        self._api_scheduler = api_scheduler

    async def __call__(
        self,
        command: EnsureRuntimeJobsCommand,
        context: RuntimeCommandHandlerContext,
    ) -> EnsureRuntimeJobsCommandResult:
        created_count = 0
        existing_count = 0
        scheduled_count = 0

        for definition in RUNTIME_JOB_DEFINITIONS:
            job = await context.uow.runtime_repository.get_job_by_key(
                definition.job_key,
            )

            if job is None:
                job = RuntimeJob.create(
                    job_type=definition.job_type,
                    job_key=definition.job_key,
                    cron_expression=definition.cron_expression,
                    metadata={},
                )
                await context.uow.runtime_repository.add_job(job)
                created_count += 1
            else:
                existing_count += 1

                if job.cron_expression != definition.cron_expression:
                    job.cron_expression = definition.cron_expression
                    await context.uow.runtime_repository.update_job(job)

            if command.register_scheduler_jobs and job.is_enabled():
                await self._api_scheduler.schedule_cron_operation(
                    ApiScheduledCronOperation(
                        operation_key=definition.job_key,
                        cron_expression=definition.cron_expression,
                        handler_key=definition.handler_key,
                        payload=definition.payload,
                        owner_user_id=None,
                    )
                )
                scheduled_count += 1

        logger.info(
            "runtime_jobs_ensured",
            created_count=created_count,
            existing_count=existing_count,
            scheduled_count=scheduled_count,
            register_scheduler_jobs=command.register_scheduler_jobs,
        )

        return EnsureRuntimeJobsCommandResult(
            created_count=created_count,
            existing_count=existing_count,
            scheduled_count=scheduled_count,
        )