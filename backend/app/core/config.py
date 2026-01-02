from typing import List, Optional
from pydantic import field_validator, EmailStr
from pydantic_settings import BaseSettings
import json


class Settings(BaseSettings):
    PROJECT_NAME: str = "Bangladesh Election Monitoring System"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Real-time election monitoring system for Bangladesh"
    
    # Database
    DATABASE_URL: str
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Admin
    FIRST_SUPERUSER_EMAIL: EmailStr
    FIRST_SUPERUSER_PASSWORD: str
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()