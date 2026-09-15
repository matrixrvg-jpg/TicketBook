from pydantic import BaseModel
from datetime import datetime

class MVPEventCreate(BaseModel):
    tenant_id: int
    title: str
    date: datetime
    max_capacity: int

class EventResponse(BaseModel):
    id: int
    tenant_id: int
    title: str
    date: datetime
    max_capacity: int
    base_price: int | None = None
    is_active: bool | None = None

    class Config:
        from_attributes = True

class TicketResponse(BaseModel):
    id: int
    seat_number: str | None = None
    status: str
    version_id: int

    class Config:
        from_attributes = True
