from pydantic import BaseModel
from datetime import datetime

class MVPEventCreate(BaseModel):
    title: str
    venue: str | None = "TBD"
    date: datetime
    max_capacity: int

class EventResponse(BaseModel):
    id: int
    tenant_id: int
    title: str
    venue: str | None = "TBD"
    date: datetime
    max_capacity: int
    base_price: int | None = None
    is_active: bool | None = None
    sold_tickets: int = 0

    class Config:
        from_attributes = True

class TicketResponse(BaseModel):
    id: int
    section: str | None = None
    seat_number: str | None = None
    status: str
    version_id: int

    class Config:
        from_attributes = True
