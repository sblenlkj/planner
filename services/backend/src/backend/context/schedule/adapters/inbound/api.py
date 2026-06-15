from __future__ import annotations

from datetime import date
from typing import Annotated
from uuid import UUID

from direttore import ModularDirettoreWithSimpleSession
from fastapi import APIRouter, Depends

from backend.bootstrap.direttore import get_direttore
from backend.context.schedule.adapters.inbound.schemas import (
    CreateDeadlineRequest,
    CreateDeadlineResponse,
    CreateReminderRequest,
    CreateReminderResponse,
    CreateScheduleDateObservationRequest,
    CreateScheduleDateObservationResponse,
    CreateScheduleDayObservationRequest,
    CreateScheduleDayObservationResponse,
    DeadlineResponse,
    ListCommitmentsResponse,
    ListScheduleDateObservationsResponse,
    ListScheduleDayObservationsResponse,
    ReminderResponse,
    ScheduleDateObservationResponse,
    ScheduleDayObservationResponse,
)
from backend.context.schedule.application.queries import (
    CommitmentKindFilter,
    GetScheduleDayQuery,
    GetScheduleDayQueryResult,
    ListScheduleDateObservationsQuery,
    ListScheduleDateObservationsQueryResult,
    ListUserCommitmentsQuery,
    ListUserCommitmentsQueryResult,
)
from backend.context.schedule.application.use_cases import (
    CreateDeadlineCommand,
    CreateDeadlineCommandResult,
    CreateReminderCommand,
    CreateReminderCommandResult,
    CreateScheduleDateObservationCommand,
    CreateScheduleDateObservationCommandResult,
    CreateScheduleDayObservationCommand,
    CreateScheduleDayObservationCommandResult,
)
from backend.context.schedule.domain.commitment.value_objects.commitment_status import (
    CommitmentStatus,
)
from backend.context.schedule.domain.shared.schedule_date import ScheduleDate


router = APIRouter(
    prefix="/schedule",
    tags=["schedule"],
)

DirettoreDep = Annotated[
    ModularDirettoreWithSimpleSession,
    Depends(get_direttore),
]


@router.post(
    "/reminders",
    response_model=CreateReminderResponse,
)
async def create_reminder(
    request: CreateReminderRequest,
    direttore: DirettoreDep,
) -> CreateReminderResponse:
    result = await direttore.handle(
        CreateReminderCommand(
            user_id=request.user_id,
            remind_at=request.remind_at_local,
            title=request.title,
            description=request.description,
        )
    )

    if not isinstance(result, CreateReminderCommandResult):
        raise TypeError(
            "CreateReminderCommand returned unexpected result type. "
            f"Got {type(result).__module__}.{type(result).__qualname__}."
        )

    return CreateReminderResponse(
        reminder_id=result.reminder_id,
    )


@router.post(
    "/deadlines",
    response_model=CreateDeadlineResponse,
)
async def create_deadline(
    request: CreateDeadlineRequest,
    direttore: DirettoreDep,
) -> CreateDeadlineResponse:
    result = await direttore.handle(
        CreateDeadlineCommand(
            user_id=request.user_id,
            due_at=request.due_at,
            title=request.title,
            description=request.description,
        )
    )

    if not isinstance(result, CreateDeadlineCommandResult):
        raise TypeError(
            "CreateDeadlineCommand returned unexpected result type. "
            f"Got {type(result).__module__}.{type(result).__qualname__}."
        )

    return CreateDeadlineResponse(
        deadline_id=result.deadline_id,
    )


@router.get(
    "/commitments",
    response_model=ListCommitmentsResponse,
)
async def list_commitments(
    user_id: UUID,
    direttore: DirettoreDep,
    status: CommitmentStatus | None = None,
    kind: CommitmentKindFilter | None = None,
) -> ListCommitmentsResponse:
    result = await direttore.handle_query(
        ListUserCommitmentsQuery(
            user_id=user_id,
            status=status,
            kind=kind,
        )
    )

    if not isinstance(result, ListUserCommitmentsQueryResult):
        raise TypeError(
            "ListUserCommitmentsQuery returned unexpected result type. "
            f"Got {type(result).__module__}.{type(result).__qualname__}."
        )

    return ListCommitmentsResponse(
        reminders=[
            ReminderResponse(
                id=reminder.id,
                user_id=reminder.user_id,
                remind_at=reminder.remind_at,
                title=reminder.title,
                description=reminder.description,
                status=reminder.status,
            )
            for reminder in result.reminders
        ],
        deadlines=[
            DeadlineResponse(
                id=deadline.id,
                user_id=deadline.user_id,
                due_at=deadline.due_at,
                title=deadline.title,
                description=deadline.description,
                status=deadline.status,
            )
            for deadline in result.deadlines
        ],
    )


@router.post(
    "/date-observations",
    response_model=CreateScheduleDateObservationResponse,
)
async def create_date_observation(
    request: CreateScheduleDateObservationRequest,
    direttore: DirettoreDep,
) -> CreateScheduleDateObservationResponse:
    result = await direttore.handle(
        CreateScheduleDateObservationCommand(
            user_id=request.user_id,
            starts_on=_to_schedule_date(request.starts_on),
            ends_on=(
                _to_schedule_date(request.ends_on)
                if request.ends_on is not None
                else None
            ),
            description=request.description,
        )
    )

    if not isinstance(result, CreateScheduleDateObservationCommandResult):
        raise TypeError(
            "CreateScheduleDateObservationCommand returned unexpected result type. "
            f"Got {type(result).__module__}.{type(result).__qualname__}."
        )

    return CreateScheduleDateObservationResponse(
        observation_id=result.observation_id,
    )


@router.get(
    "/date-observations",
    response_model=ListScheduleDateObservationsResponse,
)
async def list_date_observations(
    user_id: UUID,
    date: date,
    direttore: DirettoreDep,
) -> ListScheduleDateObservationsResponse:
    result = await direttore.handle_query(
        ListScheduleDateObservationsQuery(
            user_id=user_id,
            date=_to_schedule_date(date),
        )
    )

    if not isinstance(result, ListScheduleDateObservationsQueryResult):
        raise TypeError(
            "ListScheduleDateObservationsQuery returned unexpected result type. "
            f"Got {type(result).__module__}.{type(result).__qualname__}."
        )

    return ListScheduleDateObservationsResponse(
        observations=[
            ScheduleDateObservationResponse(
                id=observation.id,
                user_id=observation.user_id,
                starts_on=observation.starts_on.to_date(),
                ends_on=(
                    observation.ends_on.to_date()
                    if observation.ends_on is not None
                    else None
                ),
                description=observation.description,
            )
            for observation in result.observations
        ],
    )


@router.post(
    "/day-observations",
    response_model=CreateScheduleDayObservationResponse,
)
async def create_day_observation(
    request: CreateScheduleDayObservationRequest,
    direttore: DirettoreDep,
) -> CreateScheduleDayObservationResponse:
    result = await direttore.handle(
        CreateScheduleDayObservationCommand(
            user_id=request.user_id,
            date=_to_schedule_date(request.date),
            description=request.description,
        )
    )

    if not isinstance(result, CreateScheduleDayObservationCommandResult):
        raise TypeError(
            "CreateScheduleDayObservationCommand returned unexpected result type. "
            f"Got {type(result).__module__}.{type(result).__qualname__}."
        )

    return CreateScheduleDayObservationResponse(
        observation_id=result.observation_id,
    )


@router.get(
    "/day-observations",
    response_model=ListScheduleDayObservationsResponse,
)
async def list_day_observations(
    user_id: UUID,
    date: date,
    direttore: DirettoreDep,
) -> ListScheduleDayObservationsResponse:
    result = await direttore.handle_query(
        GetScheduleDayQuery(
            user_id=user_id,
            date=_to_schedule_date(date),
            include_observations=True,
        )
    )

    if not isinstance(result, GetScheduleDayQueryResult):
        raise TypeError(
            "GetScheduleDayQuery returned unexpected result type. "
            f"Got {type(result).__module__}.{type(result).__qualname__}."
        )

    if result.schedule_day is None:
        return ListScheduleDayObservationsResponse(
            observations=[],
        )

    return ListScheduleDayObservationsResponse(
        observations=[
            ScheduleDayObservationResponse(
                id=observation.id,
                user_id=result.schedule_day.user_id,
                date=result.schedule_day.date.to_date(),
                description=observation.description,
            )
            for observation in result.schedule_day.observations
        ],
    )


def _to_schedule_date(value: date) -> ScheduleDate:
    return ScheduleDate(
        year=value.year,
        month=value.month,
        day=value.day,
    )