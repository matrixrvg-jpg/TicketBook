import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.database import engine, Base
import app.models  # Ensure all models are loaded

async def reset_database():
    print("⚠️ WARNING: This will completely wipe all Users, Tenants, Events, and Tickets from the database.")
    confirmation = input("Are you sure you want to proceed? (yes/no): ")
    
    if confirmation.lower() != "yes":
        print("Aborting database reset.")
        return

    async with engine.begin() as conn:
        print("🗑️ Dropping all tables...")
        await conn.run_sync(Base.metadata.drop_all)
        
        print("🏗️ Recreating all tables...")
        await conn.run_sync(Base.metadata.create_all)
        
    print("✅ Database successfully reset to a clean state!")

if __name__ == "__main__":
    asyncio.run(reset_database())
