from datetime import date, datetime
from uuid import UUID, uuid4

from telegram_gateway.application.ports.backend_client import (
    BackendClient,
    UserRuntimeStatus,
)


class MockBackendClient(BackendClient):
    def __init__(
        self,
        default_runtime_status: UserRuntimeStatus = UserRuntimeStatus.NOT_READY,
    ) -> None:
        self._default_runtime_status = default_runtime_status
        self._statuses: dict[UUID, UserRuntimeStatus] = {}
        self._last_session_at: dict[UUID, datetime] = {}
        self._generated_days: dict[UUID, list[date]] = {}

    async def create_business_user(self) -> UUID:
        business_user_id = uuid4()
        self._statuses[business_user_id] = self._default_runtime_status
        print(
            "MockBackendClient.create_business_user:",
            {
                "business_user_id": str(business_user_id),
                "runtime_status": self._default_runtime_status.value,
            },
        )
        return business_user_id

    async def get_user_runtime_status(
        self,
        business_user_id: UUID,
    ) -> UserRuntimeStatus:
        status = self._statuses.get(business_user_id, self._default_runtime_status)
        print(
            "MockBackendClient.get_user_runtime_status:",
            {"business_user_id": str(business_user_id), "runtime_status": status.value},
        )
        return status

    async def update_user_runtime_status(
        self,
        business_user_id: UUID,
        status: UserRuntimeStatus,
    ) -> UserRuntimeStatus:
        self._statuses[business_user_id] = status
        print(
            "MockBackendClient.update_user_runtime_status:",
            {"business_user_id": str(business_user_id), "runtime_status": status.value},
        )
        return status

    async def update_user_last_session_at(
        self,
        business_user_id: UUID,
        last_session_at: datetime,
    ) -> None:
        self._last_session_at[business_user_id] = last_session_at
        print(
            "MockBackendClient.update_user_last_session_at:",
            {
                "business_user_id": str(business_user_id),
                "last_session_at": last_session_at.isoformat(),
            },
        )

    async def generate_day_schedule(
        self,
        business_user_id: UUID,
        day: date,
    ) -> None:
        self._generated_days.setdefault(business_user_id, []).append(day)
        print(
            "MockBackendClient.generate_day_schedule:",
            {"business_user_id": str(business_user_id), "day": day.isoformat()},
        )
