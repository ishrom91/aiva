from typing import Any, Dict, List
from enum import Enum
from .base import BaseSkill, PermissionLevel
from ..services.booking_service import BookingService
from ..repositories.booking_repo import BookingRepository
from sqlalchemy.ext.asyncio import AsyncSession


class BookingSkillState(Enum):
    """States for the booking FSM"""
    CHOOSE_SERVICE = "choose_service"
    CHOOSE_DATE = "choose_date"
    CHOOSE_TIME = "choose_time"
    CONFIRMATION = "confirmation"


class BookingSkill(BaseSkill):
    """
    Skill for handling booking/appointment scheduling functionality.
    Allows users to schedule appointments with beauty professionals.
    """
    
    def __init__(self, booking_service: BookingService):
        super().__init__(
            name="booking",
            description="Handles appointment booking functionality for beauty professionals"
        )
        self.booking_service = booking_service
    
    async def can_handle(self, event: Dict[str, Any]) -> bool:
        """
        Determine if this skill can handle the given event.
        Handles booking-related commands and callbacks.
        """
        # Check if event contains booking-related command or callback
        if event.get("type") == "message":
            text = event.get("text", "").lower()
            return any(cmd in text for cmd in ["/book", "/booking", "записаться", "запись"])
        elif event.get("type") == "callback_query":
            callback_data = event.get("data", "")
            return any(state.value in callback_data for state in BookingSkillState)
        return False
    
    async def handle(self, event: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle booking-related events.
        """
        # Get the current state from context
        state = context.get("state", BookingSkillState.CHOOSE_SERVICE.value)
        
        # Create a database session for this handler
        db_session: AsyncSession = context.get("db_session")
        if not db_session:
            raise ValueError("Database session is required for booking skill")
        
        # Route to appropriate handler based on state
        if state == BookingSkillState.CHOOSE_SERVICE.value:
            return await self._handle_choose_service(event, context, db_session)
        elif state == BookingSkillState.CHOOSE_DATE.value:
            return await self._handle_choose_date(event, context, db_session)
        elif state == BookingSkillState.CHOOSE_TIME.value:
            return await self._handle_choose_time(event, context, db_session)
        elif state == BookingSkillState.CONFIRMATION.value:
            return await self._handle_confirmation(event, context, db_session)
        else:
            # Default to service selection if state is unknown
            return await self._handle_choose_service(event, context, db_session)
    
    async def _handle_choose_service(self, event: Dict[str, Any], context: Dict[str, Any], db_session: AsyncSession) -> Dict[str, Any]:
        """Handle service selection step"""
        user_id = context.get("user_id")
        
        # Get master's services
        services = await self.booking_service.get_master_services(db_session, user_id)
        
        if not services:
            return {
                "type": "message",
                "text": "К сожалению, пока нет доступных услуг для записи.",
                "reply_markup": None
            }
        
        # Create inline keyboard with services
        keyboard = []
        row = []
        for i, service in enumerate(services):
            row.append({
                "text": f"{service.name} ({service.duration_minutes} мин)",
                "callback_data": f"service_{service.id}"
            })
            if len(row) == 2:  # Two buttons per row
                keyboard.append(row)
                row = []
        
        if row:  # Add remaining buttons
            keyboard.append(row)
        
        return {
            "type": "message",
            "text": "Выберите услугу:",
            "reply_markup": {
                "inline_keyboard": keyboard
            }
        }
    
    async def _handle_choose_date(self, event: Dict[str, Any], context: Dict[str, Any], db_session: AsyncSession) -> Dict[str, Any]:
        """Handle date selection step"""
        # Extract service_id from callback
        callback_data = event.get("data", "")
        if callback_data.startswith("service_"):
            service_id = int(callback_data.split("_")[1])
            context["selected_service_id"] = service_id
        
        # Generate calendar for next 14 days
        dates = await self.booking_service.get_available_dates(db_session, context.get("selected_service_id"))
        
        # Create inline keyboard with dates
        keyboard = []
        row = []
        for i, date in enumerate(dates):
            row.append({
                "text": date.strftime("%d.%m"),
                "callback_data": f"date_{date.strftime('%Y-%m-%d')}"
            })
            if len(row) == 3:  # Three buttons per row
                keyboard.append(row)
                row = []
        
        if row:  # Add remaining buttons
            keyboard.append(row)
        
        return {
            "type": "message",
            "text": "Выберите дату:",
            "reply_markup": {
                "inline_keyboard": keyboard
            }
        }
    
    async def _handle_choose_time(self, event: Dict[str, Any], context: Dict[str, Any], db_session: AsyncSession) -> Dict[str, Any]:
        """Handle time selection step"""
        # Extract date from callback
        callback_data = event.get("data", "")
        if callback_data.startswith("date_"):
            date_str = callback_data.split("_", 1)[1]
            context["selected_date"] = date_str
        
        # Get available time slots for selected date and service
        time_slots = await self.booking_service.get_available_time_slots(
            db_session,
            context.get("selected_service_id"),
            context.get("selected_date")
        )
        
        # Create inline keyboard with time slots
        keyboard = []
        row = []
        for i, slot in enumerate(time_slots):
            row.append({
                "text": slot.strftime("%H:%M"),
                "callback_data": f"time_{slot.strftime('%H:%M')}"
            })
            if len(row) == 4:  # Four buttons per row
                keyboard.append(row)
                row = []
        
        if row:  # Add remaining buttons
            keyboard.append(row)
        
        return {
            "type": "message",
            "text": "Выберите время:",
            "reply_markup": {
                "inline_keyboard": keyboard
            }
        }
    
    async def _handle_confirmation(self, event: Dict[str, Any], context: Dict[str, Any], db_session: AsyncSession) -> Dict[str, Any]:
        """Handle booking confirmation step"""
        # Extract time from callback
        callback_data = event.get("data", "")
        if callback_data.startswith("time_"):
            time_str = callback_data.split("_", 1)[1]
            context["selected_time"] = time_str
        
        # Combine date and time to get full datetime
        selected_datetime = f"{context['selected_date']} {context['selected_time']}:00"
        
        # Create the booking
        booking = await self.booking_service.create_booking(
            db_session=db_session,
            client_telegram_id=context.get("user_id"),
            service_id=context.get("selected_service_id"),
            datetime_str=selected_datetime
        )
        
        if booking:
            return {
                "type": "message",
                "text": f"✅ Ваша запись успешно создана!\n\nУслуга: {booking.service.name}\nДата: {booking.datetime.strftime('%d.%m.%Y %H:%M')}",
                "reply_markup": None
            }
        else:
            return {
                "type": "message",
                "text": "❌ Не удалось создать запись. Пожалуйста, попробуйте снова.",
                "reply_markup": None
            }
    
    def get_required_permissions(self) -> List[PermissionLevel]:
        """Return the permissions required for this skill"""
        return [PermissionLevel.REGISTERED]
    
    def get_supported_commands(self) -> List[str]:
        """Return list of supported commands"""
        return ["/book", "/booking"]