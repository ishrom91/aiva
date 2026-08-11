"""Event logging middleware for Aiva AI Bot."""

import asyncio
from datetime import datetime
from typing import Any, Callable

import structlog
from aiogram import BaseMiddleware
from aiogram.types import Update

from ..config import settings
from ..database import get_session  # Updated import
from ..models.interaction import Interaction, InteractionDirection
from ..utils.anonymization import extract_time_metadata, generate_client_hash


class EventLoggerMiddleware(BaseMiddleware):
    """Middleware for logging all interactions (event sourcing)."""

    def __init__(self):
        super().__init__()
        self.logger = structlog.get_logger(__name__)

    async def __call__(self, handler: Callable, event: Update, data: dict) -> Any:
        """Process the event and log the interaction in the background."""
        # Call the handler first and return its result immediately (non-blocking)
        result = await handler(event, data)

        # Schedule the logging task to run in the background
        if settings.DATA_COLLECTION_ENABLED:
            asyncio.create_task(self._log_interaction(event, data))

        return result

    async def _log_interaction(self, event: Update, data: dict):
        """Log the interaction in the background."""
        try:
            # Check if data collection is enabled
            if not settings.DATA_COLLECTION_ENABLED:
                return

            # Determine event type based on the event
            event_type = self._get_event_type(event)

            # Extract telegram_id from the event
            telegram_id = self._get_telegram_id(event)
            if not telegram_id:
                return  # Skip logging if we can't identify the user

            # Generate client hash using anonymization utility
            # Use the salt from settings
            client_hash = generate_client_hash(telegram_id, settings.CLIENT_HASH_SALT)

            # Get master_id from context or data
            master_id = self._get_master_id(data)
            if not master_id:
                return  # Skip logging if we can't identify the master

            # Collect metadata - calling extract_time_metadata without parameters for now
            # Since the implementation is not provided, we'll call it with current datetime
            extracted_data = extract_time_metadata(
                datetime.now()
            )  # Pass current datetime

            metadata = {
                "time_of_day": extracted_data.get("time_of_day"),
                "day_of_week": extracted_data.get("day_of_week"),
                "hour": extracted_data.get("hour"),
            }

            # Extract message length if available (not the actual text!)
            message_text_length = 0
            if hasattr(event, "message") and event.message and event.message.text:
                message_text_length = len(event.message.text)
            elif hasattr(event, "text"):
                message_text_length = len(event.text)

            metadata["message_text_length"] = message_text_length

            # Log actual text only if explicitly enabled (not for production!)
            if settings.DATA_COLLECTION_LOG_TEXT:
                text_content = ""
                if hasattr(event, "message") and event.message and event.message.text:
                    text_content = event.message.text
                elif hasattr(event, "text"):
                    text_content = event.text
                metadata["text_content"] = text_content

            # Determine interaction direction
            direction = InteractionDirection.INBOUND  # For now, assume inbound

            # Create interaction record fields
            interaction_fields = {
                "event_type": event_type,
                "master_id": master_id,
                "client_hash": client_hash,
                "direction": direction,
                "event_metadata": metadata,
            }

            # Try to extract additional fields if available
            if hasattr(event, "message") and event.message:
                # If it's a message event, try to extract service info
                interaction_fields["skill_name"] = data.get("current_skill", None)

            # Create a database session and save the interaction
            # Since the repo methods are not fully implemented, we'll need to use direct ORM operations
            async with get_session() as session:
                interaction = Interaction(**interaction_fields)
                session.add(interaction)
                await session.commit()

        except Exception as e:
            # Log any exceptions but don't crash the bot
            self.logger.exception("Failed to log interaction", error=str(e))

    def _get_event_type(self, event: Update) -> str:
        """Determine event type from the event object."""
        if event.message:
            return "message_received"
        elif event.callback_query:
            return "callback_query_received"
        elif event.inline_query:
            return "inline_query_received"
        elif event.chosen_inline_result:
            return "chosen_inline_result"
        elif event.shipping_query:
            return "shipping_query"
        elif event.pre_checkout_query:
            return "pre_checkout_query"
        elif event.poll:
            return "poll"
        elif event.poll_answer:
            return "poll_answer"
        else:
            return "unknown_event"

    def _get_telegram_id(self, event: Update) -> int | None:
        """Extract telegram ID from the event."""
        if event.message and event.message.from_user:
            return event.message.from_user.id
        elif event.callback_query and event.callback_query.from_user:
            return event.callback_query.from_user.id
        elif event.inline_query and event.inline_query.from_user:
            return event.inline_query.from_user.id
        elif event.chosen_inline_result and event.chosen_inline_result.from_user:
            return event.chosen_inline_result.from_user.id
        elif event.shipping_query and event.shipping_query.from_user:
            return event.shipping_query.from_user.id
        elif event.pre_checkout_query and event.pre_checkout_query.from_user:
            return event.pre_checkout_query.from_user.id
        elif event.poll_answer and event.poll_answer.user:
            return event.poll_answer.user.id
        else:
            return None

    def _get_master_id(self, data: dict) -> str | None:
        """Extract master ID from the context data."""
        # Try to get master_id from various sources in the data
        if "master" in data and hasattr(data["master"], "id"):
            return data["master"].id
        elif "master_id" in data:
            return data["master_id"]
        elif "state" in data and "master" in data["state"]:
            return data["state"]["master"]
        elif "booking" in data and hasattr(data["booking"], "master_id"):
            return data["booking"].master_id
        else:
            # If we can't find master_id, we can't log the interaction
            return None
