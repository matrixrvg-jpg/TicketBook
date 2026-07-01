# app/services/reservation.py
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.ticket import TicketRepository

class ReservationService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.ticket_repo = TicketRepository(db_session)

    async def attempt_ticket_reservation(self, event_id: int, user_id: int) -> int:
        """
        Stateless reservation request. 
        Delegates concurrency resolution to the database engine.
        """
        
        # 1. Fire the atomic allocation request
        reserved_ticket_id = await self.ticket_repo.reserve_any_available_ticket(
            event_id=event_id, 
            user_id=user_id
        )

        # 2. Handle the sold-out state
        if not reserved_ticket_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No available tickets remaining for this event."
            )

        # 3. Return the successfully claimed ticket ID
        return reserved_ticket_id