"""
PassiveGuard Backend Configuration
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "PassiveGuard"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Security
    SECRET_KEY: str = "passiveguard-secret-key-change-in-production"
    TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    
    # CORS
    CORS_ORIGINS: list = ["*"]
    
    # ML Model
    MODEL_PATH: str = "models/bot_detector.joblib"
    MODEL_THRESHOLD: float = 0.5
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    # Redis (optional)
    REDIS_URL: Optional[str] = None
    
    # Challenge Settings
    CHALLENGE_TIMEOUT: int = 60  # seconds
    CHALLENGE_THRESHOLD: float = 0.3  # If confidence < this, require challenge
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
