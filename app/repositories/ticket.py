from sqlalchemy import text
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseWriteRepository, BaseReadRepository
from app.models.ticket import Ticket
from sqlalchemy import select

class GetTicket(BaseReadRepository[Ticket]):
    def __init__(self, db_session: AsyncSession):
        super().__init__(Ticket, db_session)

    async def list_tickets_by_event(self, event_id: int) -> list[Ticket]:
        stmt = select(self.model).where(
            self.model.event_id == event_id
        ).order_by(self.model.id)
        result = await self.db_session.execute(stmt)
        tickets = list(result.scalars().all())
        
        # Virtual Eviction: Mask expired tickets as AVAILABLE for the frontend map
        now = datetime.now(timezone.utc)
        for t in tickets:
            if t.status == 'RESERVED' and t.expires_at and t.expires_at < now:
                # We don't commit this, we just safely mutate the Python object
                t.status = 'AVAILABLE'
                
        return tickets

class TicketRepository(BaseWriteRepository[Ticket]):
    def __init__(self, db_session: AsyncSession):
        super().__init__(model=Ticket, db_session=db_session)

    async def reserve_any_available_ticket(self, event_id: int, user_id: int) -> int | None:
        """
        ATOMIC INVENTORY ALLOCATION:
        Uses PostgreSQL's native SKIP LOCKED to find the first unlocked, 
        available ticket and reserves it in exactly one network trip.
        """
        raw_query = text("""
            UPDATE tickets
            SET status = 'RESERVED',
                user_id = :user_id,
                reserved_at = NOW(),
                expires_at = NOW() + INTERVAL '1 minute',
                version_id = version_id + 1
            WHERE id = (
                SELECT id FROM tickets
                WHERE event_id = :event_id 
                  AND (status = 'AVAILABLE' OR (status = 'RESERVED' AND expires_at < NOW()))
                  AND section = 'GA'
                LIMIT 1
                FOR UPDATE SKIP LOCKED
            )
            RETURNING id;
        """)

        result = await self.db_session.execute(
            raw_query, 
            {"event_id": event_id, "user_id": user_id}
        )
        
        # Will return the ticket.id if successful, or None if the event is 100% sold out
        return result.scalar_one_or_none()


        

