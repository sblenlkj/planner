from __future__ import annotations

from typing import Annotated

from direttore import ModularDirettoreWithSimpleSession
from fastapi import APIRouter, Depends

from backend.bootstrap.direttore import get_direttore
from backend.context.runtime.adapters.inbound.schemas import (
    RequestDayGenerationHttpStatus,
    RequestDayGenerationRequest,
    RequestDayGenerationResponse,
)
from backend.context.runtime.application.services.day_generation_request_service import (
    DayGenerationRequestStatus,
)
from backend.context.runtime.application.use_cases import (
    RequestUserDayGenerationCommand,
    RequestUserDayGenerationCommandResult,
)


router = APIRouter(
    prefix="/runtime",
    tags=["runtime"],
)

DirettoreDep = Annotated[
    ModularDirettoreWithSimpleSession,
    Depends(get_direttore),
]


@router.post(
    "/day-generation/request",
    response_model=RequestDayGenerationResponse,
)
async def request_day_generation(
    request: RequestDayGenerationRequest,
    direttore: DirettoreDep,
) -> RequestDayGenerationResponse:
    result = await direttore.handle(
        RequestUserDayGenerationCommand(
            user_id=request.business_user_id,
            day=request.day,
        )
    )

    if not isinstance(result, RequestUserDayGenerationCommandResult):
        raise TypeError(
            "RequestUserDayGenerationCommand returned unexpected result type. "
            f"Got {type(result).__module__}.{type(result).__qualname__}."
        )

    generation_result = result.result

    if generation_result.status == DayGenerationRequestStatus.PUBLISHED:
        return RequestDayGenerationResponse(
            business_user_id=generation_result.user_id,
            day=generation_result.day,
            status=RequestDayGenerationHttpStatus.QUEUED,
            reason=None,
            stream_id=generation_result.stream_id,
            event_id=generation_result.event_id,
        )

    return RequestDayGenerationResponse(
        business_user_id=generation_result.user_id,
        day=generation_result.day,
        status=RequestDayGenerationHttpStatus.SKIPPED,
        reason=generation_result.status.value,
        stream_id=generation_result.stream_id,
        event_id=generation_result.event_id,
    )