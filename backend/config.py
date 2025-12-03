"""
Configuration module for FastAPI backend.
Loads environment variables and provides configuration settings.

Security Notes:
- In production, SUPABASE_SERVICE_KEY should NOT be set
- Only SUPABASE_ANON_KEY should be used for user operations
- The service key bypasses RLS policies and is a security risk
"""
import os
import logging
from typing import Optional, List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration validation fails."""
    
    def __init__(self, message: str, errors: List[str]):
        self.message = message
        self.errors = errors
        super().__init__(self.message)


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
    
    @property
    def has_service_key(self) -> bool:
        """Check if service key is configured."""
        return bool(self.supabase_service_key)
    
    @property
    def has_anon_key(self) -> bool:
        """Check if anon key is configured."""
        return bool(self.supabase_anon_key)
    
    def validate_production_config(self) -> List[str]:
        """
        Validate configuration for production environment.
        
        Returns:
            List of warning/error messages. Empty list means valid.
        """
        issues = []
        
        if not self.is_production:
            return issues
        
        # In production, service key should NOT be set
        if self.supabase_service_key:
            issues.append(
                "SECURITY WARNING: SUPABASE_SERVICE_KEY is set in production. "
                "This bypasses RLS policies and is a security risk. "
                "Remove SUPABASE_SERVICE_KEY from production environment."
            )
        
        # In production, anon key MUST be set
        if not self.supabase_anon_key:
            issues.append(
                "ERROR: SUPABASE_ANON_KEY is required in production for user authentication."
            )
        
        # In production, SUPABASE_URL must be set
        if not self.supabase_url:
            issues.append(
                "ERROR: SUPABASE_URL is required in production."
            )
        
        return issues
    
    def verify_key_configuration(self) -> dict:
        """
        Verify Supabase key configuration and return status.
        
        This method checks the current key configuration and returns
        information about what keys are available and any warnings.
        
        Returns:
            dict with:
                - environment: Current environment
                - has_service_key: Whether service key is configured
                - has_anon_key: Whether anon key is configured
                - is_valid: Whether configuration is valid for the environment
                - warnings: List of warning messages
                - errors: List of error messages
        """
        warnings = []
        errors = []
        
        # Check production-specific issues
        if self.is_production:
            if self.supabase_service_key:
                warnings.append(
                    "SUPABASE_SERVICE_KEY is set in production - RLS will be bypassed"
                )
            if not self.supabase_anon_key:
                errors.append(
                    "SUPABASE_ANON_KEY is required in production"
                )
        else:
            # Development warnings
            if self.supabase_service_key:
                warnings.append(
                    "Using SUPABASE_SERVICE_KEY in development - RLS bypassed for service key operations"
                )
            if not self.supabase_anon_key:
                warnings.append(
                    "SUPABASE_ANON_KEY not configured - user-scoped operations unavailable"
                )
        
        is_valid = len(errors) == 0
        if self.is_production:
            # In production, also require no service key for full validity
            is_valid = is_valid and not self.supabase_service_key
        
        return {
            "environment": self.environment,
            "has_service_key": self.has_service_key,
            "has_anon_key": self.has_anon_key,
            "is_valid": is_valid,
            "warnings": warnings,
            "errors": errors
        }
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from environment


# Global settings instance
settings = Settings()


def validate_startup_configuration() -> None:
    """
    Validate configuration on application startup.
    
    This function should be called during application startup to ensure
    the configuration is valid for the current environment.
    
    Raises:
        ConfigurationError: If critical configuration errors are found in production
    """
    config_status = settings.verify_key_configuration()
    
    # Log warnings
    for warning in config_status["warnings"]:
        logger.warning(warning)
    
    # Log errors
    for error in config_status["errors"]:
        logger.error(error)
    
    # In production, fail startup if there are errors
    if settings.is_production and config_status["errors"]:
        raise ConfigurationError(
            "Production configuration validation failed",
            config_status["errors"]
        )
    
    # Log configuration summary
    logger.info(
        f"Configuration validated: environment={config_status['environment']}, "
        f"has_anon_key={config_status['has_anon_key']}, "
        f"has_service_key={config_status['has_service_key']}, "
        f"is_valid={config_status['is_valid']}"
    )
