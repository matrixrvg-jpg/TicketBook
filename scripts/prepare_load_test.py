import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.tenant import Tenant
from app.models.event import Event
from app.models.ticket import Ticket
from app.repositories.event import EventRepository
import bcrypt

async def prepare_load_test_data():
    async with AsyncSessionLocal() as db:
        print("--- Preparing Database for Extreme Load Testing ---")
        
        # 1. Ensure 100 load test users exist
        print("Seeding 100 Load Test Users...")
        pwd_bytes = "password123".encode('utf-8')
        salt = bcrypt.gensalt()
        dummy_hash = bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')
        
        for i in range(1, 101):
            email = f"loadtest{i}@ticketbook.com"
            user_check = await db.execute(select(User).where(User.email == email))
            if not user_check.scalar_one_or_none():
                db.add(User(email=email, hashed_password=dummy_hash, role="ATTENDEE", is_active=True))
        await db.commit()

        # 2. Create a massive load test event using our CTE super-query
        from datetime import datetime, timedelta, timezone

        print("Generating 'The Great Load Test' Event with 5,000 tickets...")
        repo = EventRepository(db)
        
        # Force user 1 to be a tenant just so they can own the event
        tenant_check = await db.execute(select(Tenant).where(Tenant.name == "Load Test Corp"))
        tenant = tenant_check.scalar_one_or_none()
        if not tenant:
            tenant = Tenant(name="Load Test Corp", business_email="loadtest@corp.com")
            db.add(tenant)
            await db.commit()
            await db.refresh(tenant)

        # Let's delete old load test events to keep it clean
        old_events = await db.execute(select(Event).where(Event.title == "The Great Load Test Stadium Tour"))
        for old in old_events.scalars().all():
            await db.delete(old)
        await db.commit()
            
        event_id = await repo.create_event_and_tickets_atomically(
            tenant_id=tenant.id,
            title="The Great Load Test Stadium Tour",
            venue="AWS Us-East-1 Server Farm",
            date=datetime.now(timezone.utc) + timedelta(days=30),
            max_capacity=5000
        )
        
        # WE MUST COMMIT THE TRANSACTION TO SAVE THE 5000 TICKETS
        await db.commit()
        
        # Get one VIP ticket ID for the stampede test
        vip_ticket_result = await db.execute(
            select(Ticket.id).where(Ticket.event_id == event_id).where(Ticket.section == "VIP").limit(1)
        )
        vip_ticket_id = vip_ticket_result.scalar_one_or_none()

        print(f"\nSUCCESS! Generated Event ID: {event_id} | Target VIP Ticket ID: {vip_ticket_id}")
        
        # Auto-update locustfile.py
        locustfile_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "load_tests", "locustfile.py")
        with open(locustfile_path, 'r') as file:
            data = file.readlines()
            
        for i, line in enumerate(data):
            if line.strip().startswith("TARGET_EVENT_ID"):
                data[i] = f"    TARGET_EVENT_ID = {event_id} \n"
            elif line.strip().startswith("TARGET_SPECIFIC_TICKET_ID"):
                data[i] = f"    TARGET_SPECIFIC_TICKET_ID = {vip_ticket_id} \n"
                
        with open(locustfile_path, 'w') as file:
            file.writelines(data)
            
        print("locustfile.py has been automatically updated with these IDs. You are ready to start Swarming!")

if __name__ == "__main__":
    asyncio.run(prepare_load_test_data())
