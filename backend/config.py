"""
Configuration module for FastAPI backend.
Loads environment variables and provides configuration settings.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Supabase Configuration
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_service_key: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    supabase_anon_key: str = os.getenv("SUPABASE_ANON_KEY", "")
    
    # AWS Configuration
    aws_region: str = os.getenv("AWS_REGION", "us-east-1")
    aws_profile: Optional[str] = os.getenv("AWS_PROFILE")
    
    # Bedrock Configuration
    bedrock_model_id: str = os.getenv("BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0")
    
    # API Configuration
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    
    # Environment Configuration
    environment: str = os.getenv("ENVIRONMENT", "development")
    
    # System User Configuration (for testing)
    system_user_id: str = os.getenv("SYSTEM_USER_ID", "00000000-0000-0000-0000-000000000000")
    
    # CORS Configuration
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
    
    # Retry Configuration
    max_retry_attempts: int = 3
    base_retry_delay: float = 1.0
    max_retry_delay: float = 10.0
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from environment


# Global settings instance
settings = Settings()
