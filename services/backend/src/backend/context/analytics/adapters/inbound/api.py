from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from direttore import ModularDirettoreWithSimpleSession
from fastapi import APIRouter, Depends

from backend.bootstrap.direttore import get_direttore
from backend.context.analytics.adapters.inbound.schemas import (
    AnalyticsObservationResponse,
    CreateAnalyticsObservationRequest,
    CreateAnalyticsObservationResponse,
    ListAnalyticsObservationsResponse,
)
from backend.context.analytics.application.use_cases import (
    CreateAnalyticsObservationCommand,
    CreateAnalyticsObservationCommandResult,
    ListAnalyticsObservationsCommand,
)
from backend.context.analytics.application.dto.analytics_read_models import (
    AnalyticsObservationsResult,
)
from backend.context.analytics.domain.value_objects.analytics_record_status import (
    AnalyticsRecordStatus,
)
from backend.context.analytics.domain.value_objects.analytics_scope import AnalyticsScope


router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
)

DirettoreDep = Annotated[
    ModularDirettoreWithSimpleSession,
    Depends(get_direttore),
]


@router.post(
    "/observations",
    response_model=CreateAnalyticsObservationResponse,
)
async def create_analytics_observation(
    request: CreateAnalyticsObservationRequest,
    direttore: DirettoreDep,
) -> CreateAnalyticsObservationResponse:
    result = await direttore.handle(
        CreateAnalyticsObservationCommand(
            user_id=request.user_id,
            scope=request.scope,
            description=request.description,
            evidence=request.evidence,
            confidence=request.confidence,
            importance=request.importance,
            stability=request.stability,
            tags=tuple(request.tags),
            source=request.source,
            source_id=request.source_id,
            observed_at=datetime.now(UTC),
            valid_until=request.valid_until,
        )
    )

    if not isinstance(result, CreateAnalyticsObservationCommandResult):
        raise TypeError(
            "CreateAnalyticsObservationCommand returned unexpected result "
            "type. "
            f"Got {type(result).__module__}.{type(result).__qualname__}."
        )

    return CreateAnalyticsObservationResponse(
        observation_id=result.observation_id,
    )


@router.get(
    "/observations",
    response_model=ListAnalyticsObservationsResponse,
)
async def list_analytics_observations(
    user_id: UUID,
    direttore: DirettoreDep,
    scope: AnalyticsScope | None = None,
    status: AnalyticsRecordStatus | None = AnalyticsRecordStatus.ACTIVE,
    min_confidence: float | None = None,
    min_importance: float | None = None,
    limit: int | None = 20,
) -> ListAnalyticsObservationsResponse:
    result = await direttore.handle(
        ListAnalyticsObservationsCommand(
            user_id=user_id,
            scopes=(scope,) if scope is not None else None,
            statuses=(status,) if status is not None else None,
            min_confidence=min_confidence,
            min_importance=min_importance,
            limit=limit,
        )
    )

    if not isinstance(result, AnalyticsObservationsResult):
        raise TypeError(
            "ListAnalyticsObservationsCommand returned unexpected result "
            "type. "
            f"Got {type(result).__module__}.{type(result).__qualname__}."
        )

    return ListAnalyticsObservationsResponse(
        observations=[
            AnalyticsObservationResponse.from_read_model(observation)
            for observation in result.observations
        ]
    )
