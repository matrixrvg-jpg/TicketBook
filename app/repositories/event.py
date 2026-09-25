from datetime import datetime
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

# 1. Clean imports: Pull exactly what we need, and pull Event globally so it exists at runtime.
from app.repositories.base import BaseReadRepository, BaseWriteRepository
from app.models.event import Event
from app.models.ticket import Ticket
from sqlalchemy import func

class GetEvent(BaseReadRepository[Event]):
    def __init__(self, db_session: AsyncSession):
        super().__init__(Event, db_session)

    def soft_delete(self, event: Event):
        event.is_active = False

    def restore(self, event: Event):
        event.is_active = True

    async def list_active_events(self) -> list[dict]:
        # 1. Subquery to count reserved tickets per event
        subq = (
            select(Ticket.event_id, func.count(Ticket.id).label("sold_count"))
            .where(Ticket.status == "RESERVED")
            .group_by(Ticket.event_id)
            .subquery()
        )

        # 2. Main query joining the events table with the subquery
        stmt = (
            select(self.model, func.coalesce(subq.c.sold_count, 0))
            .outerjoin(subq, self.model.id == subq.c.event_id)
            .where(self.model.is_active == True)
        )
    
        # 3. Execute non-blocking I/O flight over the connection pool stream
        result = await self.db_session.execute(stmt)
    
        # 4. Map the ORM object and the count into a clean dictionary for FastAPI
        events_data = []
        for event_obj, sold_count in result.all():
            event_dict = {
                "id": event_obj.id,
                "tenant_id": event_obj.tenant_id,
                "title": event_obj.title,
                "date": event_obj.date,
                "max_capacity": event_obj.max_capacity,
                "base_price": event_obj.base_price,
                "is_active": event_obj.is_active,
                "sold_tickets": sold_count
            }
            events_data.append(event_dict)
            
        return events_data

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
            INSERT INTO tickets (event_id, section, seat_number, status, version_id)
            SELECT
                new_event.id,
                CASE WHEN series.num <= :half_capacity THEN 'GA' ELSE 'VIP' END,
                CASE WHEN series.num <= :half_capacity THEN 'GA-' || series.num ELSE 'VIP-' || (series.num - :half_capacity) END,
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
                "half_capacity": max_capacity // 2
            },
        )

        # Return the newly created event ID
        return result.scalar()

