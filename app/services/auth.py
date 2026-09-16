import jwt
from datetime import datetime, timedelta, timezone
import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.config import settings
from app.schemas.auth import UserCreate, UserLogin, Token
from app.models.user import User
from app.models.user_tenant_ref import UserTenantRef
from app.repositories.user import UserReadRepository, UserWriteRepository
from sqlalchemy import select



class AuthService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.read_repo = UserReadRepository(db_session)
        self.write_repo = UserWriteRepository(db_session)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )

    def get_password_hash(self, password: str) -> str:
        pwd_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

    def create_access_token(self, data: dict, expires_delta: timedelta | None = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        # PyJWT 2.x encoding
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt

    async def register_user(self, user_data: UserCreate) -> User:
        existing_user = await self.read_repo.get_by_email(user_data.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        hashed_pwd = self.get_password_hash(user_data.password)
        new_user = User(
            email=user_data.email,
            hashed_password=hashed_pwd,
            role=user_data.role
        )
        
        await self.write_repo.create(new_user)
        await self.db_session.commit()
        await self.db_session.refresh(new_user)
        return new_user

    async def authenticate_user(self, login_data: UserLogin) -> Token:
        user = await self.read_repo.get_by_email(login_data.email)
        if not user or not user.hashed_password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not self.verify_password(login_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check for tenant association
        stmt = select(UserTenantRef).where(UserTenantRef.user_id == user.id)
        result = await self.db_session.execute(stmt)
        tenant_ref = result.scalar_one_or_none()
        tenant_id = tenant_ref.tenant_id if tenant_ref else None

        # Generate JWT Token
        token_payload = {"sub": str(user.id), "role": user.role}
        if tenant_id:
            token_payload["tenant_id"] = tenant_id

        access_token = self.create_access_token(data=token_payload)
        return Token(access_token=access_token, token_type="bearer")
