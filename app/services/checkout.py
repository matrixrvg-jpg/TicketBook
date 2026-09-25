from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timezone, timedelta
import logging

from app.models.ticket import Ticket

logger = logging.getLogger(__name__)

class CheckoutService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def reserve_ticket(self, ticket_id: int, user_id: int, max_retries: int = 3) -> Ticket:
        """
        Attempts to reserve a specific ticket using Optimistic Concurrency Control (OCC).
        """
        for attempt in range(max_retries):
            # 1. Read Phase: Fetch the exact ticket requested
            stmt = select(Ticket).where(Ticket.id == ticket_id)
            result = await self.db_session.execute(stmt)
            ticket = result.scalar_one_or_none()
            
            if not ticket:
                raise ValueError("Ticket does not exist.")
                
            now = datetime.now(timezone.utc)
            is_available = ticket.status == "AVAILABLE"
            is_expired = ticket.status == "RESERVED" and ticket.expires_at and ticket.expires_at < now
            
            if not (is_available or is_expired):
                raise ValueError("High Demand: Someone else grabbed this seat! Try another.")
            
            current_version = ticket.version_id
            
            # 2. Write Phase: The OCC update
            update_stmt = (
                update(Ticket)
                .where(
                    Ticket.id == ticket.id,
                    Ticket.version_id == current_version # The OCC Guard
                )
                .values(
                    status="RESERVED",
                    user_id=user_id,
                    version_id=current_version + 1,
                    reserved_at=datetime.now(timezone.utc),
                    expires_at=datetime.now(timezone.utc) + timedelta(minutes=2)
                )
                .execution_options(synchronize_session=False)
            )
            
            update_result = await self.db_session.execute(update_stmt)
            
            if update_result.rowcount == 1:
                # Success! We beat any concurrent threads.
                await self.db_session.commit()
                # Refresh to get the updated state
                await self.db_session.refresh(ticket)
                return ticket
            
            # If rowcount == 0, another thread updated this specific ticket first.
            logger.warning(f"OCC Conflict on Ticket {ticket.id}. Attempt {attempt + 1} of {max_retries}.")
            
            # The transaction is still safe, we just loop and try to grab the NEXT available ticket.
            
        raise ValueError("High Demand: Unable to secure a ticket due to concurrency. Please try again.")

    async def reserve_random_ticket(self, event_id: int, user_id: int) -> Ticket:
        """
        Attempts to reserve any available ticket using SKIP LOCKED.
        """
        from app.repositories.ticket import TicketRepository
        repo = TicketRepository(self.db_session)
        
        ticket_id = await repo.reserve_any_available_ticket(event_id, user_id)
        
        if not ticket_id:
            raise ValueError("Event is completely Sold Out!")
            
        await self.db_session.commit()
        
        # Fetch the newly reserved ticket to return
        stmt = select(Ticket).where(Ticket.id == ticket_id)
        result = await self.db_session.execute(stmt)
        return result.scalar_one()

    async def confirm_ticket(self, ticket_id: int, user_id: int, attendee_name: str | None = None, attendee_age: int | None = None) -> Ticket:
        stmt = select(Ticket).where(Ticket.id == ticket_id)
        result = await self.db_session.execute(stmt)
        ticket = result.scalar_one_or_none()
        
        if not ticket:
            raise ValueError("Ticket not found.")
            
        if ticket.user_id != user_id:
            raise ValueError("You do not own this reservation.")
            
        if ticket.status == "CONFIRMED":
            return ticket # Already confirmed
            
        if ticket.status != "RESERVED":
            raise ValueError("Ticket is not in a reserved state.")
            
        now = datetime.now(timezone.utc)
        if ticket.expires_at and ticket.expires_at < now:
            raise ValueError("Cart Timer Expired. This ticket was released back to the public pool.")
            
        # Write Phase
        current_version = ticket.version_id
        update_stmt = (
            update(Ticket)
            .where(
                Ticket.id == ticket.id,
                Ticket.version_id == current_version
            )
            .values(
                status="CONFIRMED",
                version_id=current_version + 1,
                attendee_name=attendee_name,
                attendee_age=attendee_age
            )
            .execution_options(synchronize_session=False)
        )
        
        update_result = await self.db_session.execute(update_stmt)
        if update_result.rowcount != 1:
            raise ValueError("Concurrency conflict during confirmation. Please try again.")
            
        await self.db_session.commit()
        await self.db_session.refresh(ticket)
        return ticket
