from pydantic import BaseModel
from typing import Optional

class TicketReserveRequest(BaseModel):
    ticket_id: int
    user_id: int # Assume a user is logged in for the resume MVP

class TicketRandomReserveRequest(BaseModel):
    event_id: int
    user_id: int

class TicketReserveResponse(BaseModel):
    status: str
    message: str
    ticket_id: Optional[int] = None
    reserved_at: Optional[str] = None
