"""Repository for interaction event sourcing."""

from datetime import datetime, timedelta

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.interaction import Interaction


class InteractionRepo:
    """Repository class for interaction operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, **fields: object) -> Interaction:
        """Create a new interaction record."""
        interaction = Interaction(**fields)
        self.session.add(interaction)
        await self.session.commit()
        await self.session.refresh(interaction)
        return interaction

    async def list_by_master(
        self,
        master_id: str,
        *,
        event_type: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
    ) -> list[Interaction]:
        query = select(Interaction).where(Interaction.master_id == master_id)
        conditions = []
        if start_date:
            conditions.append(Interaction.created_at >= start_date)
        if end_date:
            conditions.append(Interaction.created_at <= end_date)
        if event_type:
            conditions.append(Interaction.event_type == event_type)
        if conditions:
            query = query.where(and_(*conditions))
        query = query.order_by(Interaction.created_at.desc()).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_recent(self, master_id: str, hours: int = 24) -> list[Interaction]:
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        return await self.list_by_master(
            master_id, start_date=start_time, end_date=end_time
        )
