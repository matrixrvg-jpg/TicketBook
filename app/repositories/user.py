from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.repositories.base import BaseReadRepository, BaseWriteRepository

class UserReadRepository(BaseReadRepository[User]):
    def __init__(self, db_session: AsyncSession):
        super().__init__(User, db_session)

    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

class UserWriteRepository(BaseWriteRepository[User]):
    def __init__(self, db_session: AsyncSession):
        super().__init__(User, db_session)
