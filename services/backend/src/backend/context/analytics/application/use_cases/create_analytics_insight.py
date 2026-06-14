from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from direttore import AbstractCommandHandler, Command

from backend.context.analytics.application.orchestration import (
    AnalyticsCommandHandlerContext,
    command_handler_registry,
)
from backend.context.analytics.domain.entities.analytics_insight import AnalyticsInsight
from backend.context.analytics.domain.value_objects.analytics_scope import AnalyticsScope
from backend.context.analytics.domain.value_objects.analytics_stability import (
    AnalyticsStability,
)


@dataclass(frozen=True, kw_only=True)
class CreateAnalyticsInsightCommand(Command):
    user_id: UUID
    scope: AnalyticsScope
    description: str
    source_observation_ids: tuple[UUID, ...]
    derived_at: datetime

    evidence: str | None = None
    confidence: float = 0.7
    importance: float = 0.5
    stability: AnalyticsStability = AnalyticsStability.SHORT_TERM
    tags: tuple[str, ...] = ()

    valid_until: datetime | None = None
    id: UUID | None = None


@dataclass(frozen=True, kw_only=True)
class CreateAnalyticsInsightCommandResult:
    insight_id: UUID


@command_handler_registry.handler(CreateAnalyticsInsightCommand)
class CreateAnalyticsInsightCommandHandler(AbstractCommandHandler):
    async def __call__(
        self,
        command: CreateAnalyticsInsightCommand,
        context: AnalyticsCommandHandlerContext,
    ) -> CreateAnalyticsInsightCommandResult:
        for observation_id in command.source_observation_ids:
            observation = await context.uow.analytics_writer.get_observation_by_id(
                observation_id,
            )
            if observation is None:
                raise ValueError(f"Analytics observation not found: {observation_id}")

            if observation.user_id != command.user_id:
                raise ValueError(
                    "Analytics insight source observation belongs to another user: "
                    f"{observation_id}"
                )

        insight_id = command.id or uuid4()

        insight = AnalyticsInsight.create(
            id=insight_id,
            user_id=command.user_id,
            scope=command.scope,
            description=command.description,
            evidence=command.evidence,
            source_observation_ids=command.source_observation_ids,
            confidence=command.confidence,
            importance=command.importance,
            stability=command.stability,
            tags=command.tags,
            derived_at=command.derived_at,
            valid_until=command.valid_until,
        )

        await context.uow.analytics_writer.add_insight(
            insight=insight,
        )

        return CreateAnalyticsInsightCommandResult(
            insight_id=insight_id,
        )
