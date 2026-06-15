from uuid import UUID


class BackendClient:
    async def ensure_user_exists(
        self,
        business_user_id: UUID,
    ) -> None:
        raise NotImplementedError
