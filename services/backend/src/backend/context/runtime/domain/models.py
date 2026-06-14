from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4


class RuntimeJobType(StrEnum):
    CLOSE_SESSIONS = "close_sessions"
    BATCH_OBSERVATIONS = "batch_observations"
    GENERATE_DAY = "generate_day"
    MORNING_DELIVERY = "morning_delivery"


class RuntimeJobStatus(StrEnum):
    ENABLED = "enabled"
    DISABLED = "disabled"


class RuntimeJobExecutionSource(StrEnum):
    CRON = "cron"
    MANUAL = "manual"
    AGENT = "agent"
    SYSTEM = "system"


class RuntimeJobExecutionStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(kw_only=True, slots=True)
class RuntimeJob:
    id: UUID
    job_type: RuntimeJobType
    job_key: str
    cron_expression: str
    status: RuntimeJobStatus = RuntimeJobStatus.ENABLED
    last_run_at: datetime | None = None
    last_success_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        job_type: RuntimeJobType,
        job_key: str,
        cron_expression: str,
        metadata: dict[str, Any] | None = None,
    ) -> RuntimeJob:
        return cls(
            id=uuid4(),
            job_type=job_type,
            job_key=job_key,
            cron_expression=cron_expression,
            metadata=metadata or {},
        )

    def enable(self) -> None:
        self.status = RuntimeJobStatus.ENABLED

    def disable(self) -> None:
        self.status = RuntimeJobStatus.DISABLED

    def is_enabled(self) -> bool:
        return self.status == RuntimeJobStatus.ENABLED

    def mark_started(self, *, started_at: datetime) -> None:
        self.last_run_at = started_at

    def mark_succeeded(self, *, finished_at: datetime) -> None:
        self.last_success_at = finished_at


@dataclass(kw_only=True, slots=True)
class RuntimeJobExecution:
    id: UUID
    job_id: UUID
    source: RuntimeJobExecutionSource
    status: RuntimeJobExecutionStatus
    started_at: datetime
    finished_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def start(
        cls,
        *,
        job_id: UUID,
        source: RuntimeJobExecutionSource,
        started_at: datetime,
        metadata: dict[str, Any] | None = None,
    ) -> RuntimeJobExecution:
        return cls(
            id=uuid4(),
            job_id=job_id,
            source=source,
            status=RuntimeJobExecutionStatus.RUNNING,
            started_at=started_at,
            metadata=metadata or {},
        )

    def complete(
        self,
        *,
        finished_at: datetime,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.status = RuntimeJobExecutionStatus.COMPLETED
        self.finished_at = finished_at
        if metadata:
            self.metadata.update(metadata)

    def complete_with_warnings(
        self,
        *,
        finished_at: datetime,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.status = RuntimeJobExecutionStatus.COMPLETED_WITH_WARNINGS
        self.finished_at = finished_at
        if metadata:
            self.metadata.update(metadata)

    def fail(
        self,
        *,
        finished_at: datetime,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.status = RuntimeJobExecutionStatus.FAILED
        self.finished_at = finished_at
        if metadata:
            self.metadata.update(metadata)

    def skip(
        self,
        *,
        finished_at: datetime,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.status = RuntimeJobExecutionStatus.SKIPPED
        self.finished_at = finished_at
        if metadata:
            self.metadata.update(metadata)