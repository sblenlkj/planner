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


def test_analytics_scope_values() -> None:
    assert AnalyticsScope.EDUCATION.value == "education"
    assert AnalyticsScope.FOOD.value == "food"
    assert AnalyticsScope.SPORT.value == "sport"
    assert AnalyticsScope.PRODUCTIVITY.value == "productivity"
    assert AnalyticsScope.COMMUNICATION.value == "communication"


def test_analytics_stability_values() -> None:
    assert AnalyticsStability.SHORT_TERM.value == "short_term"
    assert AnalyticsStability.LONG_TERM.value == "long_term"


def test_analytics_record_status_values() -> None:
    assert AnalyticsRecordStatus.ACTIVE.value == "active"
    assert AnalyticsRecordStatus.REJECTED.value == "rejected"
    assert AnalyticsRecordStatus.EXPIRED.value == "expired"
    assert AnalyticsRecordStatus.SUPERSEDED.value == "superseded"


def test_analytics_observation_source_values() -> None:
    assert AnalyticsObservationSource.USER_MESSAGE.value == "user_message"
    assert AnalyticsObservationSource.AGENT_OBSERVATION.value == "agent_observation"
