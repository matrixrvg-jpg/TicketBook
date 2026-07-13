from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.tenant import Tenant
from app.repositories.base import BaseWriteRepository

class TenantRepository(BaseWriteRepository[Tenant]):
    def __init__(self, db_session: AsyncSession):
        super().__init__(model=Tenant, db_session=db_session)

    async def create_new_tenant(self, name: str, business_email: str) -> Tenant:
        new_tenant = Tenant(
            name=name,
            business_email=business_email,
            is_active=True
        )
        
        await self.create(new_tenant)
        
        try:
            # FLUSH, DO NOT COMMIT. 
            # This sends the SQL to Postgres to validate constraints, 
            # but keeps the transaction open for the Service Layer to own.
            await self.db_session.flush()
            
            # (Optional but good practice) Refresh to get the auto-generated ID
            # from the flush before returning it to the service
            await self.db_session.refresh(new_tenant)
            
            return new_tenant
            
        except IntegrityError:
            # We catch the DB-specific error and translate it to a Domain error
            raise ValueError(f"A tenant with the email '{business_email}' already exists.")