from uuid import UUID

from sqlalchemy import BigInteger, select
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from telegram_gateway.application.ports.telegram_binding_repository import (
    TelegramBindingRepository,
)
from telegram_gateway.domain.models import TelegramBinding


class Base(DeclarativeBase):
    pass


class TelegramBindingModel(Base):
    __tablename__ = "telegram_bindings"
    __table_args__ = {"schema": "telegram_gateway"}

    business_user_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
    )
    telegram_user_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False,
        index=True,
    )
    telegram_chat_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False,
        index=True,
    )


class PostgresTelegramBindingRepository(TelegramBindingRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, binding: TelegramBinding) -> None:
        self._session.add(
            TelegramBindingModel(
                business_user_id=binding.business_user_id,
                telegram_user_id=binding.telegram_user_id,
                telegram_chat_id=binding.telegram_chat_id,
            )
        )

    async def get_by_telegram_user_id(
        self,
        telegram_user_id: int,
    ) -> TelegramBinding | None:
        result = await self._session.execute(
            select(TelegramBindingModel).where(
                TelegramBindingModel.telegram_user_id == telegram_user_id,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model is not None else None

    async def get_by_business_user_id(
        self,
        business_user_id: UUID,
    ) -> TelegramBinding | None:
        result = await self._session.execute(
            select(TelegramBindingModel).where(
                TelegramBindingModel.business_user_id == business_user_id,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model is not None else None

    def _to_domain(self, model: TelegramBindingModel) -> TelegramBinding:
        return TelegramBinding(
            business_user_id=model.business_user_id,
            telegram_user_id=model.telegram_user_id,
            telegram_chat_id=model.telegram_chat_id,
        )
