"""Application configuration using Pydantic Settings."""

from pydantic import ConfigDict
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables.
    
    All settings can be configured via environment variables or .env file.
    """
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"  # Ignore extra environment variables not defined in Settings
    )
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # History Storage Configuration
    HISTORY_STORAGE_DIR: str = "data/history"
    HISTORY_MAX_FILES: int = 100
    
    # Environment
    ENVIRONMENT: str = "development"


# Global settings instance
settings = Settings()
