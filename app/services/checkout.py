from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timezone
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
                
            if ticket.status != "AVAILABLE":
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
                    reserved_at=datetime.now(timezone.utc)
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

