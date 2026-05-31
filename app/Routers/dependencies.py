from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal  # Adjust path to your project structure

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            # You can leave this blank (pass) because 'async with' 
            # automatically calls 'await session.close()' right here!
            pass
