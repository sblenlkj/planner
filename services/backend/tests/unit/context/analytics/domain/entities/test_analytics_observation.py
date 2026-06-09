from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from backend.context.analytics.domain.entities.analytics_observation import (
    AnalyticsObservation,
)
from backend.context.analytics.domain.value_objects.analytics_observation_source import (
    AnalyticsObservationSource,
)
from backend.context.analytics.domain.value_objects.analytics_record_status import (
    AnalyticsRecordStatus,
)
from backend.context.analytics.domain.value_objects.analytics_scope import AnalyticsScope
from backend.context.analytics.domain.value_objects.analytics_stability import (
    AnalyticsStability,
)


def _observed_at() -> datetime:
    return datetime(2026, 6, 9, 10, 0, tzinfo=timezone.utc)


def _make_observation(**overrides: object) -> AnalyticsObservation:
    data = {
        "user_id": uuid4(),
        "scope": AnalyticsScope.EDUCATION,
        "description": "User struggles with derivatives.",
        "evidence": "User said they do not understand derivatives.",
        "confidence": 0.8,
        "importance": 0.9,
        "stability": AnalyticsStability.SHORT_TERM,
        "tags": ("Math", " derivatives ", "math", ""),
        "source": AnalyticsObservationSource.AGENT_OBSERVATION,
        "source_id": "agent-run-1",
        "observed_at": _observed_at(),
    }
    data.update(overrides)
    return AnalyticsObservation.create(**data)


def test_create_initializes_uuid_and_active_status() -> None:
    observation = _make_observation()

    assert isinstance(observation.id, UUID)
    assert observation.status == AnalyticsRecordStatus.ACTIVE
    assert observation.is_active is True


def test_create_accepts_explicit_id() -> None:
    observation_id = uuid4()

    observation = _make_observation(id=observation_id)

    assert observation.id == observation_id


def test_create_normalizes_description_evidence_source_id_and_tags() -> None:
    observation = _make_observation(
        description="  User prefers short Python tasks.  ",
        evidence="  Based on planning discussion.  ",
        source_id="  msg-1  ",
        tags=(" Python ", "python", "Tasks", "", " tasks "),
    )

    assert observation.description == "User prefers short Python tasks."
    assert observation.evidence == "Based on planning discussion."
    assert observation.source_id == "msg-1"
    assert observation.tags == ("python", "tasks")


def test_create_converts_blank_optional_text_to_none() -> None:
    observation = _make_observation(evidence="   ", source_id="   ")

    assert observation.evidence is None
    assert observation.source_id is None


def test_create_rejects_empty_description() -> None:
    with pytest.raises(ValueError, match="description is required"):
        _make_observation(description="   ")


@pytest.mark.parametrize("field_name", ["confidence", "importance"])
def test_create_rejects_score_below_zero(field_name: str) -> None:
    with pytest.raises(ValueError, match=f"{field_name} must be between 0.0 and 1.0"):
        _make_observation(**{field_name: -0.01})


@pytest.mark.parametrize("field_name", ["confidence", "importance"])
def test_create_rejects_score_above_one(field_name: str) -> None:
    with pytest.raises(ValueError, match=f"{field_name} must be between 0.0 and 1.0"):
        _make_observation(**{field_name: 1.01})


def test_create_rejects_invalid_tags_container() -> None:
    with pytest.raises(TypeError, match="tags must be tuple"):
        _make_observation(tags=["python"])  # type: ignore[arg-type]


def test_create_rejects_non_string_tag() -> None:
    with pytest.raises(TypeError, match="each tag must be str"):
        _make_observation(tags=("python", 123))  # type: ignore[arg-type]


def test_create_rejects_valid_until_earlier_than_observed_at() -> None:
    observed_at = _observed_at()

    with pytest.raises(ValueError, match="valid_until cannot be earlier than observed_at"):
        _make_observation(
            observed_at=observed_at,
            valid_until=observed_at - timedelta(seconds=1),
        )


def test_change_description() -> None:
    observation = _make_observation()

    observation.change_description("  User now understands simple derivatives.  ")

    assert observation.description == "User now understands simple derivatives."


def test_change_evidence() -> None:
    observation = _make_observation()

    observation.change_evidence("  User solved two tasks.  ")

    assert observation.evidence == "User solved two tasks."


def test_change_scores() -> None:
    observation = _make_observation()

    observation.change_scores(confidence=0.6, importance=0.7)

    assert observation.confidence == 0.6
    assert observation.importance == 0.7


def test_change_stability() -> None:
    observation = _make_observation()

    observation.change_stability(AnalyticsStability.LONG_TERM)

    assert observation.stability == AnalyticsStability.LONG_TERM


def test_replace_tags_normalizes_and_deduplicates() -> None:
    observation = _make_observation()

    observation.replace_tags((" Asyncio ", "asyncio", "Event-Loop", ""))

    assert observation.tags == ("asyncio", "event-loop")


def test_change_source_updates_source_and_source_id() -> None:
    observation = _make_observation()

    observation.change_source(
        AnalyticsObservationSource.USER_MESSAGE,
        source_id="  message-1  ",
    )

    assert observation.source == AnalyticsObservationSource.USER_MESSAGE
    assert observation.source_id == "message-1"


def test_change_source_id() -> None:
    observation = _make_observation()

    observation.change_source_id("  message-2  ")

    assert observation.source_id == "message-2"


def test_change_observed_at() -> None:
    observation = _make_observation()

    new_observed_at = _observed_at() + timedelta(hours=1)
    observation.change_observed_at(new_observed_at)

    assert observation.observed_at == new_observed_at


def test_change_observed_at_rejects_value_after_valid_until() -> None:
    observed_at = _observed_at()
    observation = _make_observation(
        observed_at=observed_at,
        valid_until=observed_at + timedelta(hours=1),
    )

    with pytest.raises(ValueError, match="valid_until cannot be earlier than observed_at"):
        observation.change_observed_at(observed_at + timedelta(hours=2))


def test_change_valid_until() -> None:
    observation = _make_observation()

    valid_until = _observed_at() + timedelta(days=7)
    observation.change_valid_until(valid_until)

    assert observation.valid_until == valid_until


def test_change_valid_until_rejects_value_before_observed_at() -> None:
    observation = _make_observation()

    with pytest.raises(ValueError, match="valid_until cannot be earlier than observed_at"):
        observation.change_valid_until(_observed_at() - timedelta(seconds=1))


def test_reject_expire_and_activate_lifecycle() -> None:
    observation = _make_observation()

    observation.reject()
    assert observation.status == AnalyticsRecordStatus.REJECTED
    assert observation.is_active is False

    observation.activate()
    assert observation.status == AnalyticsRecordStatus.ACTIVE
    assert observation.is_active is True

    observation.expire()
    assert observation.status == AnalyticsRecordStatus.EXPIRED
    assert observation.is_active is False


def test_superseded_observation_cannot_be_rejected_expired_or_activated() -> None:
    observation = _make_observation()
    observation.status = AnalyticsRecordStatus.SUPERSEDED

    with pytest.raises(ValueError, match="superseded analytics record cannot be rejected"):
        observation.reject()

    with pytest.raises(ValueError, match="superseded analytics record cannot be expired"):
        observation.expire()

    with pytest.raises(ValueError, match="superseded analytics record cannot be activated"):
        observation.activate()
