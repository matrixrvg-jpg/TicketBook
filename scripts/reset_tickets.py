import asyncio
import sys
import os

# Add the parent directory to sys.path so we can import 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from app.database import AsyncSessionLocal
from app.models.ticket import Ticket

async def reset_tickets():
    async with AsyncSessionLocal() as db:
        print("Resetting all tickets back to AVAILABLE...")
        
        # Reset all tickets to clear out the old load test data
        stmt = (
            update(Ticket)
            .values(
                status="AVAILABLE",
                user_id=None,
                reserved_at=None
            )
        )
        
        result = await db.execute(stmt)
        await db.commit()
        
        print(f"Successfully reset {result.rowcount} tickets!")
        print("Your database is now fresh and ready for the next Chaos Test.")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(reset_tickets())
