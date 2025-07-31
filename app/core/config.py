from pydantic_settings import BaseSettings
from functools import lru_cache
from dotenv import load_dotenv
import os
from typing import Optional

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # Database settings
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "postgres")
    DB_SCHEMA: str = os.getenv("DB_SCHEMA", "public")
    DB_USER: str = os.getenv("DB_USER", "anish")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "1111")

    # OpenAI settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4")

    # API settings
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_DEBUG: bool = os.getenv("API_DEBUG", "True").lower() == "true"

    # Application settings
    DEBUG: bool = True  # Enable debug mode
    LOG_LEVEL: str = "DEBUG"  # Logging level
    LOG_TO_FILE: bool = True  # Enable file logging
    LOG_TO_CONSOLE: bool = True  # Enable console logging
    
    # Cache settings
    CACHE_ENABLED: bool = True
    CACHE_TYPE: str = "memory"  # memory or redis
    CACHE_TTL: int = 300  # 5 minutes default
    
    # Redis settings (if using Redis cache)
    REDIS_URL: Optional[str] = None

    class Config:
        env_file = ".env"

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?options=-c%20search_path%3D{self.DB_SCHEMA}"

@lru_cache()
def get_settings() -> Settings:
    return Settings() 
