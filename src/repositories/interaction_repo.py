from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from ..models import Interaction
from datetime import datetime, timedelta


class InteractionRepository:
    """Repository for handling interaction-related database operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_interaction(self, interaction: Interaction) -> Interaction:
        """Create a new interaction record"""
        self.session.add(interaction)
        await self.session.commit()
        await self.session.refresh(interaction)
        return interaction
    
    async def get_interactions_by_master(self, master_id: int, 
                                       start_date: datetime = None, 
                                       end_date: datetime = None,
                                       event_type: str = None,
                                       limit: int = 100) -> List[Interaction]:
        """Get interactions for a specific master within date range"""
        query = select(Interaction).filter(Interaction.master_id == master_id)
        
        conditions = []
        if start_date:
            conditions.append(Interaction.created_at >= start_date)
        if end_date:
            conditions.append(Interaction.created_at <= end_date)
        if event_type:
            conditions.append(Interaction.event_type == event_type)
        
        if conditions:
            query = query.filter(and_(*conditions))
        
        query = query.order_by(Interaction.created_at.desc()).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_interactions_by_client_hash(self, client_hash: str, 
                                           start_date: datetime = None, 
                                           end_date: datetime = None) -> List[Interaction]:
        """Get interactions for a specific client hash"""
        query = select(Interaction).filter(Interaction.client_hash == client_hash)
        
        conditions = []
        if start_date:
            conditions.append(Interaction.created_at >= start_date)
        if end_date:
            conditions.append(Interaction.created_at <= end_date)
        
        if conditions:
            query = query.filter(and_(*conditions))
        
        query = query.order_by(Interaction.created_at.desc())
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def count_interactions_by_type(self, master_id: int, 
                                       event_type: str, 
                                       start_date: datetime = None,
                                       end_date: datetime = None) -> int:
        """Count interactions of specific type for a master"""
        query = select(Interaction).filter(
            and_(
                Interaction.master_id == master_id,
                Interaction.event_type == event_type
            )
        )
        
        conditions = []
        if start_date:
            conditions.append(Interaction.created_at >= start_date)
        if end_date:
            conditions.append(Interaction.created_at <= end_date)
        
        if conditions:
            query = query.filter(and_(*conditions))
        
        result = await self.session.execute(query)
        return len(result.scalars().all())
    
    async def get_recent_interactions(self, master_id: int, hours: int = 24) -> List[Interaction]:
        """Get recent interactions for a master"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        query = select(Interaction).filter(
            and_(
                Interaction.master_id == master_id,
                Interaction.created_at >= start_time,
                Interaction.created_at <= end_time
            )
        ).order_by(Interaction.created_at.desc())
        
        result = await self.session.execute(query)
        return result.scalars().all()