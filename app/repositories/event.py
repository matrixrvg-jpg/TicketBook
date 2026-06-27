from ast import stmt
from unittest import result

from sqlalchemy import select 
from typing import TYPE_CHECKING
from app.repositories.base import BaseReadRepository
if TYPE_CHECKING:
    from app.models.event import Event

class GetEvent(BaseReadRepository[Event]):
    def __init__(self, db_session):
        super().__init__(Event, db_session)

    def soft_delete(self, event: Event):
        event.is_active = False

    def restore(self, event: Event):
        event.is_active = True

    async def list_active_events(self) -> list[Event]:
        # 1. Compile an explicit relational statement graph
        stmt = select(self.model).where(self.model.is_active == True)
    
        # 2. Execute non-blocking I/O flight over the connection pool stream
        result = await self.db_session.execute(stmt)
    
        # 3. Extract the clean ORM database model entities out of the cursor columns
        return list(result.scalars().all())


