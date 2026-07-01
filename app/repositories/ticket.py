# app/repositories/ticket.py
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseWriteRepository
from app.models.ticket import Ticket

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
                version_id = version_id + 1
            WHERE id = (
                SELECT id FROM tickets
                WHERE event_id = :event_id AND status = 'AVAILABLE'
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


        

