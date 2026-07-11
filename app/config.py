from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # 1. Server & System Environment Metadata
    PROJECT_NAME: str = "High-Concurrency Ticketing Engine"
    VERSION: str = "1.0.0"
    ENV: str = "development"

    # 2. Network Infrastructure & Driver URIs
    # We must explicitly use 'postgresql+psycopg' as the async scheme for your 3.14 environment
    DATABASE_URL: str = "postgresql+psycopg://postgres:gundya143@localhost:5432/ticket_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    # 3. High-Concurrency Connection Parameters (Directly matching your app/database.py names)
    DB_POOL_SIZE: int = 20             # Maps directly to settings.DB_POOL_SIZE
    DB_OVERFLOW: int = 10              # Maps directly to settings.DB_OVERFLOW
    DEBUG_SQL: bool = True             # Maps directly to settings.DEBUG_SQL

    # 4. Security, Signatures & Hashing Frameworks
    JWT_SECRET_KEY: str = "fallback_local_dev_secret_hex_string"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # 5. Continuous Configuration Strategy Layer
    # Reads a local .env file automatically if present to overwrite defaults
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore" # Prevents system-wide environment variables from clashing
    )

# CRITICAL EXPORT: Instantiates the exact 'settings' token your app modules depend on
settings = Settings()
