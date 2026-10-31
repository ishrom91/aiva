"""Repository for client operations."""

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.booking import Booking, BookingStatus
from ..models.client import Client


class ClientRepo:
    """Repository for client operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def find_dormant(
        self,
        master_id: str,
        *,
        inactive_days: int = 60,
        winback_cooldown_days: int = 30,
    ) -> list[Client]:
        cutoff = datetime.now() - timedelta(days=inactive_days)
        cooldown = datetime.now() - timedelta(days=winback_cooldown_days)

        last_visit = (
            select(
                Booking.client_id,
                func.max(Booking.datetime).label("last_visit"),
            )
            .where(
                Booking.master_id == master_id,
                Booking.status == BookingStatus.COMPLETED,
            )
            .group_by(Booking.client_id)
            .subquery()
        )

        stmt = (
            select(Client)
            .join(last_visit, Client.id == last_visit.c.client_id)
            .where(
                Client.master_id == master_id,
                last_visit.c.last_visit < cutoff,
                (Client.last_winback_at.is_(None))
                | (Client.last_winback_at < cooldown),
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def mark_winback_sent(self, client: Client) -> Client:
        client.last_winback_at = datetime.now()
        await self.session.commit()
        await self.session.refresh(client)
        return client

    async def get_by_id(self, client_id: str) -> Client | None:
        return await self.session.get(Client, client_id)
