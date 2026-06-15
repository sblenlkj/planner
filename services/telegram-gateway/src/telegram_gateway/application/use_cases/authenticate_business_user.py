from dataclasses import dataclass
from uuid import UUID

from telegram_gateway.application.ports.backend_client import BackendClient
from telegram_gateway.logging import get_logger


@dataclass(slots=True)
class AuthToken:
    access_token: str
    token_type: str = "bearer"


class AuthenticateBusinessUser:
    def __init__(
        self,
        *,
        backend_client: BackendClient,
    ) -> None:
        self._backend_client = backend_client
        self._log = get_logger(self.__class__.__name__)

    async def authenticate(
        self,
        *,
        business_user_id: UUID,
    ) -> AuthToken:
        self._log.info(
            "use_case.started",
            use_case="authenticate_business_user",
            business_user_id=str(business_user_id),
        )

        await self._backend_client.ensure_user_exists(
            business_user_id=business_user_id,
        )

        self._log.info(
            "use_case.finished",
            use_case="authenticate_business_user",
            business_user_id=str(business_user_id),
        )

        return AuthToken(access_token=str(business_user_id))
