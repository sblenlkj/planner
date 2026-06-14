from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from direttore.orchestration import ModularUnitOfWorkCoordinator

from backend.context.analytics.adapters.outbound.uow import (
    SqlAlchemyAnalyticsCommandUnitOfWork,
)
from backend.context.course.adapters.outbound.uow import (
    SqlAlchemyCourseCommandUnitOfWork,
)
from backend.context.runtime.adapters.outbound.uow import (
    SqlAlchemyRuntimeCommandUnitOfWork,
)
from backend.context.schedule.adapters.outbound.uow import (
    SqlAlchemyScheduleCommandUnitOfWork,
    SqlAlchemyScheduleQueryUnitOfWork,
)
from backend.context.user.adapters.outbound.uow import (
    SqlAlchemyUserCommandUnitOfWork,
)


class BackendUnitOfWorkCoordinator(ModularUnitOfWorkCoordinator):
    def __init__(
        self,
        *,
        session: AsyncSession,
    ) -> None:
        super().__init__()

        self.set_command_uow_factory(
            SqlAlchemyUserCommandUnitOfWork,
            lambda: SqlAlchemyUserCommandUnitOfWork(session=session),
        )

        self.set_command_uow_factory(
            SqlAlchemyRuntimeCommandUnitOfWork,
            lambda: SqlAlchemyRuntimeCommandUnitOfWork(session=session),
        )

        self.set_command_uow_factory(
            SqlAlchemyCourseCommandUnitOfWork,
            lambda: SqlAlchemyCourseCommandUnitOfWork(session=session),
        )

        self.set_command_uow_factory(
            SqlAlchemyAnalyticsCommandUnitOfWork,
            lambda: SqlAlchemyAnalyticsCommandUnitOfWork(session=session),
        )

        self.set_command_uow_factory(
            SqlAlchemyScheduleCommandUnitOfWork,
            lambda: SqlAlchemyScheduleCommandUnitOfWork(session=session),
        )

        self.set_query_uow_factory(
            SqlAlchemyScheduleQueryUnitOfWork,
            lambda: SqlAlchemyScheduleQueryUnitOfWork(session=session),
        )