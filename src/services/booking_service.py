from typing import Any


class BookingService:
    """Service class for handling booking operations."""

    async def create_booking(self, **kwargs) -> Any:
        """Create a new booking with conflict and subscription limit checks."""
        raise NotImplementedError("phase 2")

    async def get_available_slots(self, master_id: str, date: Any) -> list:
        """Get available time slots for a master on a given date."""
        raise NotImplementedError("phase 2")

    async def cancel_booking(self, booking_id: str) -> bool:
        """Cancel an existing booking."""
        raise NotImplementedError("phase 2")

    async def mark_no_show(self, booking_id: str) -> bool:
        """Mark a booking as no-show."""
        raise NotImplementedError("phase 2")


# Import moved to the top of the file to avoid circular import
