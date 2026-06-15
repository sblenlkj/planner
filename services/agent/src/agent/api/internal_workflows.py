from __future__ import annotations

from fastapi import APIRouter, Depends

from agent.api.dependencies import InternalRequestContext, get_internal_context
from agent.api.schemas import (
    ConversationRequest,
    MorningBriefingRequest,
    MorningBriefingResponse,
    WorkflowOkResponse,
)

router = APIRouter(prefix="/internal/workflows", tags=["internal-workflows"])


@router.post("/session-close/run", response_model=WorkflowOkResponse)
async def run_session_close_workflow(
    request: ConversationRequest,
    context: InternalRequestContext = Depends(get_internal_context),
) -> WorkflowOkResponse:
    # TODO:
    # 1. Run SessionSummaryWorkflow.
    # 2. Extract useful observations.
    # 3. Write analytics observations if needed.
    #
    # Telegram Gateway clears Redis only after this endpoint succeeds.
    _ = context.business_user_id
    _ = request.messages
    return WorkflowOkResponse(ok=True)


@router.post("/morning-briefing/run", response_model=MorningBriefingResponse)
async def run_morning_briefing(
    request: MorningBriefingRequest,
    context: InternalRequestContext = Depends(get_internal_context),
) -> MorningBriefingResponse:
    # TODO:
    # 1. Load user profile.
    # 2. Load courses.
    # 3. Load schedule date/day observations for request.date.
    # 4. Load active commitments.
    # 5. Generate morning briefing text.
    return MorningBriefingResponse(
        ok=True,
        assistant_text=(
            f"Доброе утро. Это тестовый morning briefing на {request.date} "
            f"для пользователя {context.business_user_id}."
        ),
    )