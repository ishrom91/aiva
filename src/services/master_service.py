"""Master onboarding and lookup helpers."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.master import Master


async def get_master_by_telegram_id(
    session: AsyncSession, telegram_id: int
) -> Master | None:
    result = await session.execute(
        select(Master).where(Master.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


async def get_or_create_master(
    session: AsyncSession,
    telegram_id: int,
    name: str,
) -> tuple[Master, bool]:
    """Return master and whether it was newly created."""
    master = await get_master_by_telegram_id(session, telegram_id)
    if master:
        return master, False

    master = Master(
        telegram_id=telegram_id,
        name=name,
        is_active=True,
        settings={},
        work_start_hour=9,
        work_end_hour=18,
    )
    session.add(master)
    await session.commit()
    await session.refresh(master)
    return master, True
