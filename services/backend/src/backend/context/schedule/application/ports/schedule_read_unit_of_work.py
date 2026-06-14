from __future__ import annotations

from typing import Protocol

from backend.context.schedule.application.ports.repositories.commitment_read_repository import (
    CommitmentReadRepository,
)

from backend.context.schedule.application.ports.repositories.template_read_repository import (
    TemplateReadRepository,
)

from backend.context.schedule.application.ports.repositories.execution_read_repository import (
    ExecutionReadRepository,
)

class ScheduleReadUnitOfWork(Protocol):
    commitment_reader: CommitmentReadRepository
    template_reader: TemplateReadRepository
    execution_reader: ExecutionReadRepository