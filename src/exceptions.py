"""Domain exceptions for Aiva AI Bot."""


class AivaError(Exception):
    """Base application error."""


class SubscriptionLimitExceeded(AivaError):
    """Raised when a master exceeds their subscription booking limit."""

    def __init__(self, message: str, upsell_text: str | None = None) -> None:
        super().__init__(message)
        self.upsell_text = upsell_text


class BookingConflictError(AivaError):
    """Raised when a booking slot is already taken."""


class OwnershipError(AivaError):
    """Raised when a user tries to access another master's resource."""
