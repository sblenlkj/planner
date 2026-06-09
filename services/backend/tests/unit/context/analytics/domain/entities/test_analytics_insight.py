from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from backend.context.analytics.domain.entities.analytics_insight import AnalyticsInsight
from backend.context.analytics.domain.value_objects.analytics_record_status import (
    AnalyticsRecordStatus,
)
from backend.context.analytics.domain.value_objects.analytics_scope import AnalyticsScope
from backend.context.analytics.domain.value_objects.analytics_stability import (
    AnalyticsStability,
)


def _derived_at() -> datetime:
    return datetime(2026, 6, 9, 12, 0, tzinfo=timezone.utc)


def _source_ids() -> tuple[UUID, UUID]:
    return uuid4(), uuid4()


def _make_insight(**overrides: object) -> AnalyticsInsight:
    observation_id_1, observation_id_2 = _source_ids()

    data = {
        "user_id": uuid4(),
        "scope": AnalyticsScope.PRODUCTIVITY,
        "description": "User works better with small concrete steps.",
        "evidence": "Several planning sessions showed better progress with small steps.",
        "source_observation_ids": (observation_id_1, observation_id_2),
        "confidence": 0.85,
        "importance": 0.9,
        "stability": AnalyticsStability.LONG_TERM,
        "tags": ("Productivity", " small-steps ", "productivity"),
        "derived_at": _derived_at(),
    }
    data.update(overrides)
    return AnalyticsInsight.create(**data)


def test_create_initializes_uuid_active_status_and_no_replacement() -> None:
    insight = _make_insight()

    assert isinstance(insight.id, UUID)
    assert insight.status == AnalyticsRecordStatus.ACTIVE
    assert insight.replaced_by is None
    assert insight.is_active is True


def test_create_accepts_explicit_id() -> None:
    insight_id = uuid4()

    insight = _make_insight(id=insight_id)

    assert insight.id == insight_id


def test_create_normalizes_text_tags_and_source_observation_ids() -> None:
    observation_id = uuid4()

    insight = _make_insight(
        description="  User prefers concise answers.  ",
        evidence="  Based on repeated feedback.  ",
        source_observation_ids=(observation_id, observation_id),
        tags=(" Communication ", "communication", "Concise", ""),
    )

    assert insight.description == "User prefers concise answers."
    assert insight.evidence == "Based on repeated feedback."
    assert insight.source_observation_ids == (observation_id,)
    assert insight.tags == ("communication", "concise")


def test_create_converts_blank_evidence_to_none() -> None:
    insight = _make_insight(evidence="   ")

    assert insight.evidence is None


def test_create_rejects_empty_description() -> None:
    with pytest.raises(ValueError, match="description is required"):
        _make_insight(description="   ")


@pytest.mark.parametrize("field_name", ["confidence", "importance"])
def test_create_rejects_score_below_zero(field_name: str) -> None:
    with pytest.raises(ValueError, match=f"{field_name} must be between 0.0 and 1.0"):
        _make_insight(**{field_name: -0.01})


@pytest.mark.parametrize("field_name", ["confidence", "importance"])
def test_create_rejects_score_above_one(field_name: str) -> None:
    with pytest.raises(ValueError, match=f"{field_name} must be between 0.0 and 1.0"):
        _make_insight(**{field_name: 1.01})


def test_create_rejects_invalid_source_observation_ids_container() -> None:
    with pytest.raises(TypeError, match="source_observation_ids must be tuple"):
        _make_insight(source_observation_ids=[uuid4()])  # type: ignore[arg-type]


def test_create_rejects_non_uuid_source_observation_id() -> None:
    with pytest.raises(TypeError, match="source_observation_id must be UUID"):
        _make_insight(source_observation_ids=(uuid4(), "bad-id"))  # type: ignore[arg-type]


def test_create_rejects_valid_until_earlier_than_derived_at() -> None:
    derived_at = _derived_at()

    with pytest.raises(ValueError, match="valid_until cannot be earlier than derived_at"):
        _make_insight(
            derived_at=derived_at,
            valid_until=derived_at - timedelta(seconds=1),
        )


def test_init_rejects_superseded_without_replaced_by() -> None:
    with pytest.raises(ValueError, match="superseded insight must have replaced_by"):
        AnalyticsInsight(
            id=uuid4(),
            user_id=uuid4(),
            scope=AnalyticsScope.EDUCATION,
            description="User has improved in Python basics.",
            evidence=None,
            source_observation_ids=(uuid4(),),
            confidence=0.8,
            importance=0.8,
            stability=AnalyticsStability.SHORT_TERM,
            status=AnalyticsRecordStatus.SUPERSEDED,
            tags=(),
            derived_at=_derived_at(),
            replaced_by=None,
        )


def test_init_rejects_non_superseded_with_replaced_by() -> None:
    with pytest.raises(ValueError, match="only superseded insight can have replaced_by"):
        AnalyticsInsight(
            id=uuid4(),
            user_id=uuid4(),
            scope=AnalyticsScope.EDUCATION,
            description="User has improved in Python basics.",
            evidence=None,
            source_observation_ids=(uuid4(),),
            confidence=0.8,
            importance=0.8,
            stability=AnalyticsStability.SHORT_TERM,
            status=AnalyticsRecordStatus.ACTIVE,
            tags=(),
            derived_at=_derived_at(),
            replaced_by=uuid4(),
        )


def test_init_rejects_self_replacement() -> None:
    insight_id = uuid4()

    with pytest.raises(ValueError, match="insight cannot be replaced by itself"):
        AnalyticsInsight(
            id=insight_id,
            user_id=uuid4(),
            scope=AnalyticsScope.EDUCATION,
            description="User has improved in Python basics.",
            evidence=None,
            source_observation_ids=(uuid4(),),
            confidence=0.8,
            importance=0.8,
            stability=AnalyticsStability.SHORT_TERM,
            status=AnalyticsRecordStatus.SUPERSEDED,
            tags=(),
            derived_at=_derived_at(),
            replaced_by=insight_id,
        )


def test_change_description() -> None:
    insight = _make_insight()

    insight.change_description("  User prefers practical Python examples.  ")

    assert insight.description == "User prefers practical Python examples."


def test_change_scores() -> None:
    insight = _make_insight()

    insight.change_scores(confidence=0.7, importance=0.6)

    assert insight.confidence == 0.7
    assert insight.importance == 0.6


def test_replace_source_observations_normalizes_and_deduplicates() -> None:
    insight = _make_insight()
    observation_id = uuid4()

    insight.replace_source_observations((observation_id, observation_id))

    assert insight.source_observation_ids == (observation_id,)


def test_add_source_observation_appends_once() -> None:
    insight = _make_insight()
    observation_id = uuid4()

    insight.add_source_observation(observation_id)
    insight.add_source_observation(observation_id)

    assert insight.source_observation_ids.count(observation_id) == 1


def test_remove_source_observation() -> None:
    observation_id = uuid4()
    other_observation_id = uuid4()
    insight = _make_insight(
        source_observation_ids=(observation_id, other_observation_id),
    )

    insight.remove_source_observation(observation_id)

    assert insight.source_observation_ids == (other_observation_id,)


def test_change_derived_at() -> None:
    insight = _make_insight()

    new_derived_at = _derived_at() + timedelta(hours=1)
    insight.change_derived_at(new_derived_at)

    assert insight.derived_at == new_derived_at


def test_change_derived_at_rejects_value_after_valid_until() -> None:
    derived_at = _derived_at()
    insight = _make_insight(
        derived_at=derived_at,
        valid_until=derived_at + timedelta(hours=1),
    )

    with pytest.raises(ValueError, match="valid_until cannot be earlier than derived_at"):
        insight.change_derived_at(derived_at + timedelta(hours=2))


def test_change_valid_until() -> None:
    insight = _make_insight()

    valid_until = _derived_at() + timedelta(days=10)
    insight.change_valid_until(valid_until)

    assert insight.valid_until == valid_until


def test_change_valid_until_rejects_value_before_derived_at() -> None:
    insight = _make_insight()

    with pytest.raises(ValueError, match="valid_until cannot be earlier than derived_at"):
        insight.change_valid_until(_derived_at() - timedelta(seconds=1))


def test_supersede_by_sets_status_and_replacement() -> None:
    insight = _make_insight()
    new_insight_id = uuid4()

    insight.supersede_by(new_insight_id)

    assert insight.status == AnalyticsRecordStatus.SUPERSEDED
    assert insight.replaced_by == new_insight_id
    assert insight.is_active is False


def test_supersede_by_rejects_self_replacement() -> None:
    insight = _make_insight()

    with pytest.raises(ValueError, match="insight cannot be superseded by itself"):
        insight.supersede_by(insight.id)


def test_supersede_by_rejects_non_active_insight() -> None:
    insight = _make_insight()
    insight.reject()

    with pytest.raises(ValueError, match="only active insight can be superseded"):
        insight.supersede_by(uuid4())


def test_reject_expire_and_activate_clear_replaced_by() -> None:
    insight = _make_insight()

    insight.reject()
    assert insight.status == AnalyticsRecordStatus.REJECTED
    assert insight.replaced_by is None

    insight.activate()
    assert insight.status == AnalyticsRecordStatus.ACTIVE

    insight.expire()
    assert insight.status == AnalyticsRecordStatus.EXPIRED
    assert insight.replaced_by is None


def test_superseded_insight_cannot_be_rejected_expired_or_activated() -> None:
    insight = _make_insight()
    insight.supersede_by(uuid4())

    with pytest.raises(ValueError, match="superseded analytics record cannot be rejected"):
        insight.reject()

    with pytest.raises(ValueError, match="superseded analytics record cannot be expired"):
        insight.expire()

    with pytest.raises(ValueError, match="superseded analytics record cannot be activated"):
        insight.activate()
