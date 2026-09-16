import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jwt.exceptions import InvalidTokenError
from typing import AsyncGenerator

from app.database import AsyncSessionLocal
from app.config import settings
from app.schemas.auth import TokenData
from app.models.user import User
from app.repositories.user import UserReadRepository

# Common Dependency to inject DB session (Adhering to SOLID Dependency Inversion)
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

# Note: We point this to the swagger-login so that FastAPI's /docs UI "Authorize" button works out of the box
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/swagger-login")

async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency that decodes the JWT token and returns the current authenticated User model.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # PyJWT decode usage
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        token_data = TokenData(user_id=int(user_id_str), role=payload.get("role"))
    except InvalidTokenError:
        raise credentials_exception
        
    user_repo = UserReadRepository(db)
    user = await user_repo.get_by_id(token_data.user_id)
    
    if user is None:
        raise credentials_exception
        
    # Dynamically fetch tenant_id
    from sqlalchemy import select
    from app.models.user_tenant_ref import UserTenantRef
    stmt = select(UserTenantRef).where(UserTenantRef.user_id == user.id)
    result = await db.execute(stmt)
    tenant_ref = result.scalar_one_or_none()
    user.tenant_id = tenant_ref.tenant_id if tenant_ref else None
    
    return user

async def get_current_organizer(current_user: User = Depends(get_current_user)) -> User:
    """
    Role-Based Access Control (RBAC) dependency. Validates user is an Organizer.
    """
    if current_user.role != "ORGANIZER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges (ORGANIZER required)"
        )
    return current_user
