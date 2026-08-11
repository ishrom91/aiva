"""Helper to log custom interaction events from handlers."""

import asyncio
from datetime import datetime

from ..config import settings
from ..database import get_session
from ..models.interaction import Interaction, InteractionDirection
from ..utils.anonymization import extract_time_metadata, generate_client_hash


async def _write_event(
    master_id: str,
    telegram_id: int,
    event_type: str,
    metadata: dict | None = None,
) -> None:
    if not settings.DATA_COLLECTION_ENABLED:
        return

    meta = extract_time_metadata(datetime.now())
    payload = {
        "time_of_day": meta.get("time_of_day"),
        "day_of_week": meta.get("day_of_week"),
        "hour": meta.get("hour"),
    }
    if metadata:
        payload.update(metadata)

    client_hash = generate_client_hash(telegram_id, settings.CLIENT_HASH_SALT)

    async with get_session() as session:
        interaction = Interaction(
            event_type=event_type,
            master_id=master_id,
            client_hash=client_hash,
            direction=InteractionDirection.INBOUND,
            event_metadata=payload,
        )
        session.add(interaction)
        await session.commit()


def log_event(
    master_id: str,
    telegram_id: int,
    event_type: str,
    metadata: dict | None = None,
) -> None:
    """Fire-and-forget event logging."""
    asyncio.create_task(_write_event(master_id, telegram_id, event_type, metadata))
