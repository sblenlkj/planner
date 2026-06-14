from __future__ import annotations

from typing import Protocol

from backend.context.schedule.application.ports.repositories.commitment_write_repository import (
    CommitmentWriteRepository,
)

from backend.context.schedule.application.ports.repositories.template_write_repository import (
    TemplateWriteRepository,
)

from backend.context.schedule.application.ports.repositories.execution_write_repository import (
    ExecutionWriteRepository,
)


class ScheduleWriteUnitOfWork(Protocol):
    commitment_writer: CommitmentWriteRepository
    template_writer: TemplateWriteRepository
    execution_writer: ExecutionWriteRepository