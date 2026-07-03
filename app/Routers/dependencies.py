from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

# Import the factory object directly, DO NOT call it with () here
from app.database import AsyncSessionLocal 

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that generates a session from the factory 
    and handles its isolated cleanup after the request.
    """
    # This is where the factory is actually called () to create a session per request
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

