from __future__ import annotations

from fastapi import APIRouter

from agent.infrastructure.observability.metrics import llm_slot_metrics

router = APIRouter(
    prefix="/internal/metrics",
    tags=["internal-metrics"],
)


@router.get("/llm-slots")
async def get_llm_slot_metrics() -> dict:
    return llm_slot_metrics.snapshot()