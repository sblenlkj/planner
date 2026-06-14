from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from direttore import AbstractCommandHandler, Command

from backend.context.analytics.application.orchestration import (
    AnalyticsCommandHandlerContext,
    command_handler_registry,
)
from backend.context.analytics.domain.entities.analytics_observation import (
    AnalyticsObservation,
)
from backend.context.analytics.domain.value_objects.analytics_observation_source import (
    AnalyticsObservationSource,
)
from backend.context.analytics.domain.value_objects.analytics_scope import AnalyticsScope
from backend.context.analytics.domain.value_objects.analytics_stability import (
    AnalyticsStability,
)


@dataclass(frozen=True, kw_only=True)
class CreateAnalyticsObservationCommand(Command):
    user_id: UUID
    scope: AnalyticsScope
    description: str
    observed_at: datetime

    evidence: str | None = None
    confidence: float = 0.7
    importance: float = 0.5
    stability: AnalyticsStability = AnalyticsStability.SHORT_TERM
    tags: tuple[str, ...] = ()

    source: AnalyticsObservationSource = AnalyticsObservationSource.AGENT_OBSERVATION
    source_id: str | None = None

    valid_until: datetime | None = None
    id: UUID | None = None


@dataclass(frozen=True, kw_only=True)
class CreateAnalyticsObservationCommandResult:
    observation_id: UUID


@command_handler_registry.handler(CreateAnalyticsObservationCommand)
class CreateAnalyticsObservationCommandHandler(AbstractCommandHandler):
    async def __call__(
        self,
        command: CreateAnalyticsObservationCommand,
        context: AnalyticsCommandHandlerContext,
    ) -> CreateAnalyticsObservationCommandResult:
        observation_id = command.id or uuid4()

        observation = AnalyticsObservation.create(
            id=observation_id,
            user_id=command.user_id,
            scope=command.scope,
            description=command.description,
            evidence=command.evidence,
            confidence=command.confidence,
            importance=command.importance,
            stability=command.stability,
            tags=command.tags,
            source=command.source,
            source_id=command.source_id,
            observed_at=command.observed_at,
            valid_until=command.valid_until,
        )

        await context.uow.analytics_writer.add_observation(
            observation=observation,
        )

        return CreateAnalyticsObservationCommandResult(
            observation_id=observation_id,
        )
