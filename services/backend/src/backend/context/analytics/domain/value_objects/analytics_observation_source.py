from enum import StrEnum


class AnalyticsObservationSource(StrEnum):
    USER_MESSAGE = "user_message"
    AGENT_OBSERVATION = "agent_observation"