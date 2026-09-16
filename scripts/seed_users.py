import asyncio
import sys
import os

# Add the parent directory to sys.path so we can import 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from app.models.user import User
from app.services.auth import AuthService
from app.schemas.auth import UserCreate
import bcrypt

async def seed_users(num_users: int = 100):
    async with AsyncSessionLocal() as db:
        print(f"Seeding {num_users} users...")
        # Optimize insertion by batching and hashing once
        pwd_bytes = "password123".encode('utf-8')
        salt = bcrypt.gensalt()
        dummy_hash = bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')
        
        for i in range(1, num_users + 1):
            email = f"loadtest{i}@ticketbook.com"
            from sqlalchemy import select
            user_check = await db.execute(select(User).where(User.email == email))
            if not user_check.scalar_one_or_none():
                db.add(User(email=email, hashed_password=dummy_hash, role="ATTENDEE", is_active=True))
                if i % 50 == 0:
                    print(f"Prepared {i} users...")
            else:
                if i % 50 == 0:
                    print(f"Skipped {i} (already exists)")
        
        await db.commit()
        print("Done!")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed_users(100)) # Just seed 100 for local testing speed
