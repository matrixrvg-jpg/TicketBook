from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

# Import your strict Bouncer schemas
from app.schemas.tenant import TenantCreate, TenantIdResponse

# Import the orchestrator service
from app.services.tenant import TenantService

# Import your database injection hook
from app.Routers.dependencies import get_db 

# Initialize the router with a prefix and Swagger UI tag
router = APIRouter(prefix="/tenants", tags=["Tenants (System Admin)"])

@router.post("/", response_model=TenantIdResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    payload: TenantCreate, 
    db_session: AsyncSession = Depends(get_db)
):
    """
    Registers a new Tenant in the multi-tenant engine.
    Returns only the newly generated Tenant ID.
    """
    # 1. Instantiate the service layer with the injected session
    service = TenantService(db_session=db_session)
    
    try:
        # 2. Hand off execution to the business logic layer
        tenant = await service.register_new_tenant(payload)
        
        # 3. Return the full object. 
        # FastAPI will use TenantIdResponse to strip away everything except the 'id'
        return tenant
        
    except ValueError as e:
        # 4. Translate Domain errors into HTTP errors
        # If the repository caught an IntegrityError (duplicate email), 
        # it raised a ValueError. We turn that into a 400 Bad Request.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=str(e)
        )