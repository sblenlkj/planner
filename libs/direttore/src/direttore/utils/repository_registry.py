from __future__ import annotations

from collections.abc import Iterator
from typing import Callable

from direttore.orchestration.base_classes.repo import TrackingRepository

class RepositoryRegistry:
    def __init__(self):
        self._factories: dict[str, Callable[..., object]] = {}
        self._instances: dict[str, object] = {}

    def register(self, key: str, factory: Callable[..., object]) -> None:
        self._factories[key] = factory

    def get_or_create(self, key: str) -> object:
        if key not in self._instances:
            factory = self._factories[key]
            self._instances[key] = factory()
        return self._instances[key]

    def iter_created(self) -> Iterator[object]:
        for repo in self._instances.values():
            if isinstance(repo, TrackingRepository):
                yield repo

    def clear(self) -> None:
        self._instances.clear()



# class InMemoryOrdersUnitOfWork(AbstractOrchestrationUnitOfWork):
#     def __init__(self, database: InMemoryOrdersDatabase) -> None:
#         self._database = database
#         self._repositories = RepositoryRegistry()

#         self.committed = False
#         self.rolled_back = False

#     @property
#     def users(self) -> UsersRepository:
#         return self._repositories.get_or_create(
#             key="users",
#             factory=lambda: InMemoryUsersRepository(self._database),
#         )

#     def _iter_repositories(self) -> Iterable[TrackingRepository]:
#         return self._repositories.iter_tracking_repositories()

#     async def run(
#         self,
#         func: Callable[[], Awaitable[TResult]],
#     ) -> TResult:
#         try:
#             result = await func()
#         except Exception:
#             self.rolled_back = True
#             raise

#         self.committed = True
#         return result