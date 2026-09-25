from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

# Import the exact dependency generator you just built
from app.dependencies import get_db, get_current_organizer

# Import your services and read repositories
from app.services.tenant_mgmt import TenantManagementService
from app.repositories.event import GetEvent


router = APIRouter(prefix="/events", tags=["Events (MVP Test)"])

from app.schemas.events import MVPEventCreate, EventResponse, TicketResponse
from app.repositories.ticket import GetTicket
# ---------------------------------------------------------
# POST: The Write Path (Command)
# ---------------------------------------------------------
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_event_endpoint(
    payload: MVPEventCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_organizer)
):
    """
    MVP Testing Endpoint: Creates an event and its inventory via the CTE query.
    """
    if not current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Organizer must create a business profile first")

    # 1. Instantiate the business orchestrator
    service = TenantManagementService(db_session=db)
    
    try:
        # 2. Fire the workflow (this triggers your raw CTE query)
        new_event_id = await service.execute_event_onboarding_workflow(
            tenant_id=current_user.tenant_id,
            title=payload.title,
            venue=payload.venue,
            date=payload.date,
            max_capacity=payload.max_capacity
        )
        
        # 3. Commit the transaction to disk
        await db.commit()
        
        return {
            "status": "success",
            "message": f"Event {new_event_id} and {payload.max_capacity} tickets successfully generated.",
            "event_id": new_event_id
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=str(e)
        )


# for getting events 
@router.get("/dashboard", status_code=status.HTTP_200_OK, response_model=dict[str, str | int | list[EventResponse]])
async def list_dashboard_events_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_organizer)
):
    """
    Private endpoint: Fetches active events only for the logged-in Organizer.
    """
    if not current_user.tenant_id:
        return {"status": "success", "count": 0, "data": []}

    read_repo = GetEvent(db_session=db)
    # The existing list_active_events method needs to be filtered by tenant_id.
    # For now, we will fetch all and filter in Python, but we should update GetEvent to accept tenant_id.
    events = await read_repo.list_active_events()
    my_events = [e for e in events if e["tenant_id"] == current_user.tenant_id]
    
    return {
        "status": "success",
        "count": len(my_events),
        "data": my_events
    }

@router.get("/public", status_code=status.HTTP_200_OK, response_model=dict[str, str | int | list[EventResponse]])
async def list_public_events_endpoint(
    db: AsyncSession = Depends(get_db)
):
    """
    Public endpoint: Fetches all active events across all tenants for the frontpage.
    """
    read_repo = GetEvent(db_session=db)
    events = await read_repo.list_active_events()
    
    return {
        "status": "success",
        "count": len(events),
        "data": events
    }

@router.get("/{event_id}/tickets", status_code=status.HTTP_200_OK, response_model=dict[str, str | int | list[TicketResponse]])
async def list_event_tickets_endpoint(
    event_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Returns the exact tickets for an event to build the true Seat Map.
    """
    read_repo = GetTicket(db_session=db)
    tickets = await read_repo.list_tickets_by_event(event_id)
    
    return {
        "status": "success",
        "count": len(tickets),
        "data": tickets
    }