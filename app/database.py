from alembic.environment import Any
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.config import settings

# 1. The Async Engine: The core connection to PostgreSQL
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG_SQL,           # Set to True in local dev to see raw SQL queries
    future=True,                       # Enforces SQLAlchemy 2.0 semantics
    pool_size=settings.DB_POOL_SIZE,   # Baseline number of persistent connections (e.g., 20)
    max_overflow=settings.DB_OVERFLOW, # Allowable temporary connections during extreme spikes (e.g., 10)
    pool_timeout=30.0,                 # How long a request waits for a free connection before failing
)

# 2. The Session Factory: Generates transient sessions for transactions
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    expire_on_commit=False, # CRITICAL: Prevents SQLAlchemy from issuing a blocking secondary SELECT after a commit
)

# 3. The Declarative Base: The registry for all domain models (Tenant, Event, Ticket)
Base:Any = declarative_base()