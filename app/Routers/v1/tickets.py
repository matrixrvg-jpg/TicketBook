from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.Routers.dependencies import get_db
from app.services.reservation import ReservationService

router = APIRouter(prefix="/tickets", tags=["Tickets (MVP Test)"])

# 1. Dirty/Inline Schema: Just enough to make FastAPI accept a JSON body
class MVPReserveRequest(BaseModel):
    event_id: int
    user_id: int  # Faking the JWT extraction by just passing it in the JSON

@router.post("/reserve", status_code=status.HTTP_201_CREATED)
async def reserve_ticket_endpoint(
    payload: MVPReserveRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    MVP Testing Endpoint: Bypasses auth to test the SKIP LOCKED database engine.
    """
    # 2. Instantiate the orchestrator
    service = ReservationService(db_session=db)
    
    # 3. Fire the atomic database operation
    # If sold out, the service will raise a 404 cleanly
    ticket_id = await service.attempt_ticket_reservation(
        event_id=payload.event_id, 
        user_id=payload.user_id
    )
    
    # 4. Commit the transaction to disk
    await db.commit()
    
    # 5. Raw dictionary response (bypassing response_model schemas)
    return {
        "status": "success",
        "message": "Ticket successfully locked and reserved.",
        "data": {
            "ticket_id": ticket_id,
            "event_id": payload.event_id,
            "owner_user_id": payload.user_id
        }
    }