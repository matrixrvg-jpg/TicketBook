from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.tenant import TenantRepository
from app.schemas.tenant import TenantCreate
from app.models.tenant import Tenant
from app.models.user_tenant_ref import UserTenantRef

class TenantService:
    def __init__(self, db_session: AsyncSession):
        self.session = db_session
        self.repo = TenantRepository(db_session=db_session)

    async def register_new_tenant(self, payload: TenantCreate, user_id: int) -> Tenant:
        """
        Orchestrates the creation of a Tenant. 
        Owns the transaction boundary (Commit/Rollback).
        """
        try:
            # 1. Ask the repo to stage the new tenant in the database
            tenant = await self.repo.create_new_tenant(
                name=payload.name,
                business_email=payload.business_email
            )
            
            # Flush to get the tenant.id generated
            await self.session.flush()

            # 2. Link the logged-in user to this new tenant
            user_tenant_ref = UserTenantRef(user_id=user_id, tenant_id=tenant.id)
            self.session.add(user_tenant_ref)
            
            # 3. Seal the Unit of Work
            await self.session.commit()
            return tenant
            
        except ValueError as e:
            # If the Repo throws our clean Domain error (like duplicate email), 
            # we roll back the transaction so the async pool isn't poisoned.
            await self.session.rollback()
            raise e
            
        except Exception as e:
            # Catch-all for any other catastrophic system failures
            await self.session.rollback()
            raise e