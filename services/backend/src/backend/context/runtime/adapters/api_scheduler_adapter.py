from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.cron import CronTrigger

from direttore import ModularDirettoreWithSimpleSession

from backend.shared.application.ports.api_scheduler import (
    ApiScheduledCronOperation,
    ApiScheduledOperation,
    ApiSchedulerPort,
)
from backend.shared.logging import get_logger


logger = get_logger(__name__)


class ApschedulerApiSchedulerAdapter(ApiSchedulerPort):
    """
    APScheduler-based implementation of ApiSchedulerPort.

    Direttore is attached after bootstrap through bind_direttore(),
    because the adapter itself may be needed while Direttore is still being built.
    """

    def __init__(
        self,
        *,
        scheduler: AsyncIOScheduler,
        timezone: str = "UTC",
        misfire_grace_time_seconds: int = 300,
    ) -> None:
        self._scheduler = scheduler
        self._direttore: ModularDirettoreWithSimpleSession | None = None
        self._timezone = timezone
        self._misfire_grace_time_seconds = misfire_grace_time_seconds

    def bind_direttore(
        self,
        direttore: ModularDirettoreWithSimpleSession,
    ) -> None:
        self._direttore = direttore

        logger.info("api_scheduler_direttore_bound")

    async def schedule_operation(
        self,
        operation: ApiScheduledOperation,
    ) -> None:
        run_at = self._normalize_run_at(operation.run_at)

        self._scheduler.add_job(
            self._run_operation,
            trigger=DateTrigger(
                run_date=run_at,
                timezone=self._timezone,
            ),
            id=operation.operation_key,
            name=self._build_job_name(operation),
            kwargs={
                "operation_key": operation.operation_key,
                "handler_key": operation.handler_key,
                "payload": operation.payload,
                "owner_user_id": (
                    str(operation.owner_user_id)
                    if operation.owner_user_id is not None
                    else None
                ),
            },
            replace_existing=True,
            misfire_grace_time=self._misfire_grace_time_seconds,
            coalesce=True,
            max_instances=1,
        )

        logger.info(
            "api_scheduler_operation_scheduled",
            operation_key=operation.operation_key,
            handler_key=operation.handler_key,
            run_at=run_at.isoformat(),
            owner_user_id=(
                str(operation.owner_user_id)
                if operation.owner_user_id is not None
                else None
            ),
        )

    async def cancel_operation(
        self,
        operation_key: str,
    ) -> None:
        try:
            self._scheduler.remove_job(operation_key)
        except JobLookupError:
            logger.info(
                "api_scheduler_operation_cancel_noop",
                operation_key=operation_key,
            )
            return

        logger.info(
            "api_scheduler_operation_cancelled",
            operation_key=operation_key,
        )


    async def schedule_cron_operation(
        self,
        operation: ApiScheduledCronOperation,
    ) -> None:
        self._scheduler.add_job(
            self._run_operation,
            trigger=CronTrigger.from_crontab(
                operation.cron_expression,
                timezone=self._timezone,
            ),
            id=operation.operation_key,
            name=self._build_cron_job_name(operation),
            kwargs={
                "operation_key": operation.operation_key,
                "handler_key": operation.handler_key,
                "payload": operation.payload,
                "owner_user_id": (
                    str(operation.owner_user_id)
                    if operation.owner_user_id is not None
                    else None
                ),
            },
            replace_existing=True,
            misfire_grace_time=self._misfire_grace_time_seconds,
            coalesce=True,
            max_instances=1,
        )

        logger.info(
            "api_scheduler_cron_operation_scheduled",
            operation_key=operation.operation_key,
            handler_key=operation.handler_key,
            cron_expression=operation.cron_expression,
            owner_user_id=(
                str(operation.owner_user_id)
                if operation.owner_user_id is not None
                else None
            ),
        )

    @staticmethod
    def _build_cron_job_name(operation: ApiScheduledCronOperation) -> str:
        return (
            f"api-cron-operation:"
            f"{operation.handler_key}:"
            f"{operation.operation_key}"
        )

    async def _run_operation(
        self,
        *,
        operation_key: str,
        handler_key: str,
        payload: dict[str, Any],
        owner_user_id: str | None,
    ) -> None:
        logger.info(
            "api_scheduler_operation_started",
            operation_key=operation_key,
            handler_key=handler_key,
            owner_user_id=owner_user_id,
        )

        try:
            await self._dispatch_operation(
                handler_key=handler_key,
                payload=payload,
            )
        except Exception:
            logger.exception(
                "api_scheduler_operation_failed",
                operation_key=operation_key,
                handler_key=handler_key,
                owner_user_id=owner_user_id,
            )
            raise

        logger.info(
            "api_scheduler_operation_completed",
            operation_key=operation_key,
            handler_key=handler_key,
            owner_user_id=owner_user_id,
        )

    async def _dispatch_operation(
        self,
        *,
        handler_key: str,
        payload: dict[str, Any],
    ) -> object:
        if self._direttore is None:
            raise RuntimeError(
                "ApschedulerApiSchedulerAdapter is not bound to Direttore. "
                "Call bind_direttore() after Direttore bootstrap is complete."
            )

        return await self._direttore.handle_by_key(
            key=handler_key,
            payload=payload,
        )

    @staticmethod
    def _normalize_run_at(run_at: datetime) -> datetime:
        if run_at.tzinfo is None:
            return run_at.replace(tzinfo=UTC)

        return run_at.astimezone(UTC)

    @staticmethod
    def _build_job_name(operation: ApiScheduledOperation) -> str:
        return (
            f"api-operation:"
            f"{operation.handler_key}:"
            f"{operation.operation_key}"
        )
    
    def start(self) -> None:
        if not self._scheduler.running:
            self._scheduler.start()


    def shutdown(self) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)