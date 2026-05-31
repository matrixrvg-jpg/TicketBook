from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    DB_POOL_SIZE: int = 20
    DB_OVERFLOW: int = 10
    DEBUG_SQL: bool = False

    # Security / Auth
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8") # tells pydantic where to look from


settings = Settings() # instantiates the Settings class 