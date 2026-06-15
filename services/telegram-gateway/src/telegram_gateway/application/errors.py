class TelegramGatewayApplicationError(Exception):
    """Base Telegram Gateway application error."""


class TelegramBindingNotFoundError(TelegramGatewayApplicationError):
    pass


class BusinessUserNotFoundError(TelegramGatewayApplicationError):
    pass


class AgentResponseError(TelegramGatewayApplicationError):
    pass


class AgentInputBlockedError(AgentResponseError):
    """Agent Server rejected user input by security/input guard policy."""

    def __init__(
        self,
        message: str = "User message was blocked by Agent Server input guard.",
        *,
        violations: list[dict] | None = None,
    ) -> None:
        super().__init__(message)
        self.violations = violations or []


class TelegramMessageDeliveryError(TelegramGatewayApplicationError):
    pass