from __future__ import annotations

from dataclasses import dataclass

from backend.context.runtime.domain.models import RuntimeJobType
from backend.context.schedule.application.reminder_runtime import (
    RUNTIME_TRIGGER_REMINDER_HANDLER_KEY 
)


CLOSE_ACTIVE_SESSIONS_JOB_KEY = "close_sessions:daily"
BATCH_OBSERVATIONS_JOB_KEY = "batch_observations:daily"
GENERATE_DAY_JOB_KEY = "generate_day:daily"
MORNING_DELIVERY_JOB_KEY = "morning_delivery:daily"

REMINDER_TRIGGER_HANDLER_KEY = RUNTIME_TRIGGER_REMINDER_HANDLER_KEY 
ENSURE_RUNTIME_JOBS_HANDLER_KEY = "runtime.ensure_runtime_jobs"
CLOSE_ACTIVE_SESSIONS_HANDLER_KEY = "runtime.close_active_sessions"
BATCH_OBSERVATIONS_HANDLER_KEY = "runtime.batch_observations"
GENERATE_DAY_HANDLER_KEY = "runtime.generate_day"
MORNING_DELIVERY_HANDLER_KEY = "runtime.morning_delivery"


CLOSE_ACTIVE_SESSIONS_CRON = "0 0 * * *"
BATCH_OBSERVATIONS_CRON = "0 2 * * *"
GENERATE_DAY_CRON = "0 3 * * *"
MORNING_DELIVERY_CRON = "0 6 * * *"


@dataclass(frozen=True, kw_only=True, slots=True)
class RuntimeJobDefinition:
    job_type: RuntimeJobType
    job_key: str
    cron_expression: str
    handler_key: str
    payload: dict[str, object]


RUNTIME_JOB_DEFINITIONS: tuple[RuntimeJobDefinition, ...] = (
    RuntimeJobDefinition(
        job_type=RuntimeJobType.CLOSE_SESSIONS,
        job_key=CLOSE_ACTIVE_SESSIONS_JOB_KEY,
        cron_expression=CLOSE_ACTIVE_SESSIONS_CRON,
        handler_key=CLOSE_ACTIVE_SESSIONS_HANDLER_KEY,
        payload={},
    ),
    RuntimeJobDefinition(
        job_type=RuntimeJobType.BATCH_OBSERVATIONS,
        job_key=BATCH_OBSERVATIONS_JOB_KEY,
        cron_expression=BATCH_OBSERVATIONS_CRON,
        handler_key=BATCH_OBSERVATIONS_HANDLER_KEY,
        payload={},
    ),
    RuntimeJobDefinition(
        job_type=RuntimeJobType.GENERATE_DAY,
        job_key=GENERATE_DAY_JOB_KEY,
        cron_expression=GENERATE_DAY_CRON,
        handler_key=GENERATE_DAY_HANDLER_KEY,
        payload={},
    ),
    RuntimeJobDefinition(
        job_type=RuntimeJobType.MORNING_DELIVERY,
        job_key=MORNING_DELIVERY_JOB_KEY,
        cron_expression=MORNING_DELIVERY_CRON,
        handler_key=MORNING_DELIVERY_HANDLER_KEY,
        payload={},
    ),
)