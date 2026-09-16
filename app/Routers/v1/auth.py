from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm

from app.schemas.auth import UserCreate, Token, UserLogin
from app.services.auth import AuthService
from app.dependencies import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Registers a new user (defaults to ORGANIZER role for this prototype) and returns a JWT token.
    """
    auth_service = AuthService(db)
    user = await auth_service.register_user(user_data)
    
    # Auto-login after successful registration to return token
    login_data = UserLogin(email=user_data.email, password=user_data.password)
    token = await auth_service.authenticate_user(login_data)
    return token


@router.post("/login", response_model=Token)
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    Authenticates a user via JSON payload (for React frontend) and returns a JWT token.
    """
    auth_service = AuthService(db)
    return await auth_service.authenticate_user(login_data)
    

@router.post("/swagger-login", response_model=Token, include_in_schema=False)
async def swagger_login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """
    Endpoint specifically built to support FastAPI's built-in Swagger UI login modal,
    which sends data as 'application/x-www-form-urlencoded' instead of JSON.
    """
    from pydantic import ValidationError
    auth_service = AuthService(db)
    try:
        login_data = UserLogin(email=form_data.username, password=form_data.password)
    except ValidationError:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Invalid email format")
    return await auth_service.authenticate_user(login_data)
