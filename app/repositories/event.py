from datetime import datetime
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

# 1. Clean imports: Pull exactly what we need, and pull Event globally so it exists at runtime.
from app.repositories.base import BaseReadRepository, BaseWriteRepository
from app.models.event import Event

class GetEvent(BaseReadRepository[Event]):
    def __init__(self, db_session: AsyncSession):
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

    # you can also use the get_by_id method from the BaseReadRepository to fetch a single event by its ID, which is already implemented in the base class.

class EventRepository(BaseWriteRepository[Event]):
    def __init__(self, db_session: AsyncSession):
        # We still inherit the generic base in case we need simple inserts later
        super().__init__(model=Event, db_session=db_session)

    async def create_event_and_tickets_atomically(
        self,
        tenant_id: int,
        title: str,
        date: datetime,
        max_capacity: int,
    ) -> int:
        """
        Executes a singular, ultra-optimized PostgreSQL query using a CTE.
        This forces the database engine to generate the tickets natively,
        bypassing Python memory array loops entirely.
        """

        # The exact raw SQL to handle everything in one database round trip
        raw_query = text("""
            WITH new_event AS (
                INSERT INTO events (tenant_id, title, date, max_capacity, is_active)
                VALUES (:tenant_id, :title, :date, :max_capacity, true)
                RETURNING id
            )
            INSERT INTO tickets (event_id, seat_number, status, version_id)
            SELECT
                new_event.id,
                'GA-Slot-' || series.num,
                'AVAILABLE',
                1
            FROM new_event,
                 generate_series(1, :max_capacity) AS series(num)
            RETURNING event_id;
        """)

        # Execute the query securely using bound parameters
        result = await self.db_session.execute(
            raw_query,
            {
                "tenant_id": tenant_id,
                "title": title,
                "date": date,
                "max_capacity": max_capacity,
            },
        )

        # Return the newly created event ID
        return result.scalar()

