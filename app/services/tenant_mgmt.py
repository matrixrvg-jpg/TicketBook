# app/services/tenant_mgmt.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.event import EventRepository
from datetime import datetime

class TenantManagementService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.event_repo = EventRepository(db_session)
        
    async def execute_event_onboarding_workflow(
        self, tenant_id: int, title: str, date: datetime, max_capacity: int
    ) -> int:
        """
        Orchestrates event creation. Because the database handles the heavy lifting
        via a CTE, we simply delegate the parameters to the optimized repository method.
        """
        
        # Note: We do not build an array here anymore!
        # We let PostgreSQL's generate_series do all the work.
        new_event_id = await self.event_repo.create_event_and_tickets_atomically(
            tenant_id=tenant_id,
            title=title,
            date=date,
            max_capacity=max_capacity
        )
        
        return new_event_id