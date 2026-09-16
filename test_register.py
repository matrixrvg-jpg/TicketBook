import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
from app.database import AsyncSessionLocal
from app.services.auth import AuthService
from app.schemas.auth import UserCreate

async def test_register():
    async with AsyncSessionLocal() as session:
        auth_service = AuthService(session)
        from app.schemas.auth import UserLogin
        login_data = UserLogin(email="test2@example.com", password="password123")
        try:
            token = await auth_service.authenticate_user(login_data)
            print("Login Success:", token.access_token)
        except Exception as e:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_register())
