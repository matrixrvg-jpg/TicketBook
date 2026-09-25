import pytest
import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import AsyncSessionLocal
from app.models.ticket import Ticket
from app.services.checkout import CheckoutService

@pytest.mark.asyncio
async def test_optimistic_concurrency_control_vip_seats():
    """
    Simulates a Taylor Swift scale event where 5 users simultaneously 
    attempt to reserve the exact same VIP seat at the exact same millisecond.
    Proves that Optimistic Concurrency Control (OCC) blocks the 4 losers.
    """
    # 1. Setup: Grab a real database connection
    async with AsyncSessionLocal() as db:
        # Find any AVAILABLE VIP ticket to be our target
        result = await db.execute(
            select(Ticket).where(Ticket.status == "AVAILABLE").where(Ticket.section == "VIP").limit(1)
        )
        target_ticket = result.scalar_one_or_none()
        
        if not target_ticket:
            pytest.skip("No AVAILABLE VIP tickets in the database to test against.")
            
        ticket_id = target_ticket.id
        
        # 2. Execution: Fire 5 simultaneous reservation attempts
        # Each attempt uses its own database session and CheckoutService
        async def attempt_purchase(user_id: int):
            async with AsyncSessionLocal() as session:
                service = CheckoutService(session)
                try:
                    await service.reserve_ticket(ticket_id=ticket_id, user_id=user_id)
                    return "SUCCESS"
                except ValueError as e:
                    # Catch the OCC Version Mismatch error
                    return "FAILED_OCC"
                except Exception:
                    return "ERROR"
                    
        # Launch 5 concurrent tasks using asyncio.gather
        results = await asyncio.gather(
            attempt_purchase(user_id=1),
            attempt_purchase(user_id=2),
            attempt_purchase(user_id=3),
            attempt_purchase(user_id=4),
            attempt_purchase(user_id=5)
        )
        
        # 3. Assertions: We expect exactly 1 winner and 4 losers
        successes = results.count("SUCCESS")
        occ_failures = results.count("FAILED_OCC")
        
        assert successes == 1, f"Expected exactly 1 success, got {successes}"
        assert occ_failures == 4, f"Expected 4 OCC blocks, got {occ_failures}"
        
        # 4. Teardown: Release the ticket so it doesn't break future tests
        # We simulate a "timer expiration" or explicit rejection
        target_ticket.status = "AVAILABLE"
        await db.commit()

@pytest.mark.asyncio
async def test_pessimistic_concurrency_skip_locked():
    """
    Simulates a General Admission queue where 5 users simultaneously click 'Buy Next Ticket'.
    Proves that PostgreSQL SKIP LOCKED allows all 5 transactions to process in parallel 
    without blocking each other, returning 5 unique tickets.
    """
    async with AsyncSessionLocal() as db:
        # Find an event that has at least 5 AVAILABLE GA tickets
        result = await db.execute(
            select(Ticket.event_id)
            .where(Ticket.status == "AVAILABLE")
            .where(Ticket.section == "GA")
            .group_by(Ticket.event_id)
            .having(func.count(Ticket.id) >= 5)
            .limit(1)
        )
        event_id = result.scalar_one_or_none()
        
        if not event_id:
            pytest.skip("No event found with at least 5 AVAILABLE GA tickets.")
            
        async def attempt_ga_purchase(user_id: int):
            async with AsyncSessionLocal() as session:
                service = CheckoutService(session)
                try:
                    ticket = await service.reserve_random_ticket(event_id=event_id, user_id=user_id)
                    return ticket.id
                except Exception as e:
                    return f"ERROR: {e}"
                    
        # Launch 5 concurrent purchases
        results = await asyncio.gather(
            attempt_ga_purchase(user_id=1),
            attempt_ga_purchase(user_id=2),
            attempt_ga_purchase(user_id=3),
            attempt_ga_purchase(user_id=4),
            attempt_ga_purchase(user_id=5)
        )
        
        # 1. Ensure all 5 requests successfully purchased a ticket (no OCC failures, no locks)
        successful_ticket_ids = [res for res in results if isinstance(res, int)]
        assert len(successful_ticket_ids) == 5, f"Expected 5 successful purchases, got {successful_ticket_ids}"
        
        # 2. Ensure all 5 tickets are completely UNIQUE (no double-bookings)
        assert len(set(successful_ticket_ids)) == 5, "Duplicate tickets were assigned!"
        
        # 3. Teardown: Release tickets back to pool
        for ticket_id in successful_ticket_ids:
            ticket = await db.get(Ticket, ticket_id)
            ticket.status = "AVAILABLE"
        await db.commit()

