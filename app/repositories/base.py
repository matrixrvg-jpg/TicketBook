from typing import Generic, TypeVar, Type, Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import Base


# Define a shared generic TypeVar bound to your SQLAlchemy declarative base model
ModelType = TypeVar("ModelType", bound=Base) 

# Base Read Repsository with common read operations
class BaseReadRepository(Generic[ModelType]):
    def __init__(self,model: Type[ModelType],db_session: AsyncSession):
        self.model = model
        self.db_session = db_session
    
    async def get_by_id(self,id:int) -> Optional[ModelType]:
        result = await self.db_session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result




# It is the write Resopsitory that will handle all the write operations like create, update and delete. It will be used by the services 
class BaseWriteRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db_session: AsyncSession):
        self.model = model
        self.db_session = db_session

    async def create(self, entity: ModelType) -> ModelType:
        self.db_session.add(entity)
        return entity

    # No delete function as we are doing soft deletes by setting is_active to False