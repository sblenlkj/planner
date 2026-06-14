from __future__ import annotations

from typing import Protocol

from backend.context.analytics.application.ports.analytics_read_repository import (
    AnalyticsReadRepository,
)
from backend.context.analytics.application.ports.analytics_write_repository import (
    AnalyticsWriteRepository,
)


class AnalyticsUnitOfWork(Protocol):
    analytics_writer: AnalyticsWriteRepository
    analytics_reader: AnalyticsReadRepository
