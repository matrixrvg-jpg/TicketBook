from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

# Import the exact dependency generator you just built
from app.Routers.dependencies import get_db 

# Import your services and read repositories
from app.services.tenant_mgmt import TenantManagementService
from app.repositories.event import GetEvent

router = APIRouter(prefix="/events", tags=["Events (MVP Test)"])

# ---------------------------------------------------------
# MVP Inline Schemas (To validate incoming JSON)
# ---------------------------------------------------------
class MVPEventCreate(BaseModel):
    tenant_id: int
    title: str
    date: datetime
    max_capacity: int


# ---------------------------------------------------------
# POST: The Write Path (Command)
# ---------------------------------------------------------
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_event_endpoint(
    payload: MVPEventCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    MVP Testing Endpoint: Creates an event and its inventory via the CTE query.
    """
    # 1. Instantiate the business orchestrator
    service = TenantManagementService(db_session=db)
    
    try:
        # 2. Fire the workflow (this triggers your raw CTE query)
        new_event_id = await service.execute_event_onboarding_workflow(
            tenant_id=payload.tenant_id,
            title=payload.title,
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
