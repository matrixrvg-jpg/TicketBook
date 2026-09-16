from pydantic import BaseModel
from typing import Optional

class TicketReserveRequest(BaseModel):
    ticket_id: int

class TicketRandomReserveRequest(BaseModel):
    event_id: int

class TicketReserveResponse(BaseModel):
    status: str
    message: str
    ticket_id: Optional[int] = None
    reserved_at: Optional[str] = None
