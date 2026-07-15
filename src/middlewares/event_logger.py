from typing import Callable, Awaitable
from aiogram import BaseMiddleware, Bot
from aiogram.types import Message, CallbackQuery, Update
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import Interaction, Master
from ..database import get_db_session
from ..utils.anonymization import generate_client_hash, extract_time_metadata
from ..config import settings
import structlog
from datetime import datetime


class EventLoggerMiddleware(BaseMiddleware):
    """
    Middleware for logging ALL events to the interactions table.
    Works asynchronously (background task), does not block the bot.
    """
    
    def __init__(self):
        super().__init__()
        self.logger = structlog.get_logger(__name__)
    
    async def __call__(
        self,
        handler: Callable,
        event: Update,
        data: dict
    ) -> None:
        # Process the event first
        result = await handler(event, data)
        
        # Then log the event asynchronously
        await self.log_event(event, data)
        
        return result
    
    async def log_event(self, event: Update, data: dict) -> None:
        """
        Log the event to the interactions table.
        """
        try:
            # Determine event type
            event_type = self._get_event_type(event)
            if not event_type:
                return  # Skip logging for events we don't track
            
            # Extract user info
            user_id = None
            if event.message:
                user_id = event.message.from_user.id
            elif event.callback_query:
                user_id = event.callback_query.from_user.id
            elif event.edited_message:
                user_id = event.edited_message.from_user.id
            
            if not user_id:
                return
            
            # Get master_id from the data context
            master_id = data.get("master_id")
            if not master_id:
                # Try to get master_id from the database based on user_id
                master_id = await self._get_master_id_by_user_id(user_id)
                if not master_id:
                    return
            
            # Generate client hash
            client_hash = generate_client_hash(user_id, settings.CLIENT_HASH_SALT)
            
            # Extract metadata
            metadata = self._extract_metadata(event, data)
            
            # Determine direction
            direction = "inbound"  # Default for user-initiated events
            
            # Determine skill name if available
            skill_name = data.get("skill_name", None)
            
            # Determine service type if applicable
            service_type = data.get("service_type", None)
            
            # Get price if applicable
            price = data.get("price", None)
            
            # Get location district if available
            location_district = data.get("location_district", None)
            
            # Create interaction record
            async with get_db_session() as session:
                interaction = Interaction(
                    event_type=event_type,
                    master_id=master_id,
                    client_hash=client_hash,
                    skill_name=skill_name,
                    direction=direction,
                    service_type=service_type,
                    price=price,
                    location_district=location_district,
                    metadata=metadata
                )
                
                session.add(interaction)
                await session.commit()
                
        except Exception as e:
            # Log the error but don't interrupt the main flow
            self.logger.error("Failed to log interaction", error=str(e), exc_info=True)
    
    def _get_event_type(self, event: Update) -> str:
        """
        Determine the event type based on the update.
        """
        if event.message:
            if event.message.text:
                return "message_received"
            elif event.message.contact:
                return "contact_shared"
            elif event.message.location:
                return "location_shared"
        elif event.callback_query:
            if event.callback_query.data.startswith("booking_"):
                return "booking_action"
            elif event.callback_query.data.startswith("service_"):
                return "service_selected"
            elif event.callback_query.data.startswith("date_"):
                return "date_selected"
            elif event.callback_query.data.startswith("time_"):
                return "time_selected"
            elif event.callback_query.data.startswith("confirm_"):
                return "booking_confirmed"
            elif event.callback_query.data.startswith("cancel_"):
                return "booking_cancelled"
            else:
                return "callback_query"
        elif event.edited_message:
            return "message_edited"
        elif event.channel_post:
            return "channel_post"
        elif event.edited_channel_post:
            return "channel_post_edited"
        elif event.inline_query:
            return "inline_query"
        elif event.chosen_inline_result:
            return "inline_result_chosen"
        elif event.shipping_query:
            return "shipping_query"
        elif event.pre_checkout_query:
            return "pre_checkout_query"
        
        return None
    
    def _extract_metadata(self, event: Update, data: dict) -> dict:
        """
        Extract metadata from the event.
        """
        metadata = {}
        
        # Add timestamp metadata
        timestamp = datetime.utcnow()
        metadata.update(extract_time_metadata(timestamp))
        
        # Add message length if applicable
        if event.message and event.message.text:
            metadata["message_text_length"] = len(event.message.text)
        
        # Add booking status if applicable
        if data.get("booking_status"):
            metadata["booking_status"] = data["booking_status"]
        
        # Add upsell info if applicable
        if data.get("upsell_tariff"):
            metadata["upsell_tariff"] = data["upsell_tariff"]
        
        # Add state info if applicable
        if data.get("state"):
            metadata["current_state"] = data["state"]
        
        return metadata
    
    async def _get_master_id_by_user_id(self, user_id: int) -> int:
        """
        Get master_id based on user_id from the database.
        """
        async with get_db_session() as session:
            # Check if user is a master first
            master_result = await session.execute(
                select(Master).filter(Master.telegram_id == user_id)
            )
            master = master_result.scalar_one_or_none()
            
            if master:
                return master.id
            
            # If not a master, user might be a client, find their master
            # This would require importing Client model and doing another query
            # For now, returning None
            return None


# Import here to avoid circular imports
from sqlalchemy import select