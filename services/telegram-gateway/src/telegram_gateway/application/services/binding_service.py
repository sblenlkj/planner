from dataclasses import dataclass
from uuid import UUID

from telegram_gateway.application.ports.backend_client import BackendClient
from telegram_gateway.application.ports.binding_cache import BindingCache
from telegram_gateway.application.ports.telegram_binding_repository import (
    TelegramBindingRepository,
)
from telegram_gateway.domain.models import TelegramBinding
from telegram_gateway.application.errors import TelegramBindingNotFoundError


@dataclass(slots=True)
class BindingResolution:
    binding: TelegramBinding
    created: bool = False


class BindingService:
    def __init__(
        self,
        *,
        backend_client: BackendClient,
        binding_cache: BindingCache | None = None,
    ) -> None:
        self._backend_client = backend_client
        self._binding_cache = binding_cache

    async def ensure_for_telegram_user(
        self,
        *,
        telegram_user_id: int,
        telegram_chat_id: int,
        telegram_bindings: TelegramBindingRepository,
    ) -> BindingResolution:
        binding = None

        if self._binding_cache is not None:
            binding = await self._binding_cache.get_by_telegram_user_id(
                telegram_user_id=telegram_user_id,
            )

        if binding is None:
            binding = await telegram_bindings.get_by_telegram_user_id(
                telegram_user_id=telegram_user_id,
            )

        if binding is not None:
            await self._cache_binding(binding)
            return BindingResolution(binding=binding, created=False)

        business_user_id = await self._backend_client.create_business_user()

        binding = TelegramBinding(
            business_user_id=business_user_id,
            telegram_user_id=telegram_user_id,
            telegram_chat_id=telegram_chat_id,
        )

        await telegram_bindings.add(binding)
        await self._cache_binding(binding)

        return BindingResolution(binding=binding, created=True)

    async def get_by_business_user_id(
        self,
        *,
        business_user_id: UUID,
        telegram_bindings: TelegramBindingRepository,
    ) -> TelegramBinding:
        binding = None

        if self._binding_cache is not None:
            binding = await self._binding_cache.get_by_business_user_id(
                business_user_id=business_user_id,
            )

        if binding is None:
            binding = await telegram_bindings.get_by_business_user_id(
                business_user_id=business_user_id,
            )

        if binding is None:
            raise TelegramBindingNotFoundError(
                f"Telegram binding was not found for business_user_id={business_user_id}"
            )

        await self._cache_binding(binding)
        return binding

    async def _cache_binding(self, binding: TelegramBinding) -> None:
        if self._binding_cache is not None:
            await self._binding_cache.set_binding(binding)
