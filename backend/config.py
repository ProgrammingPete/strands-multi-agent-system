"""
Configuration module for FastAPI backend.
Loads environment variables and provides configuration settings.

Supports two configuration sources:
1. AWS Secrets Manager (when AWS_SECRETS_NAME is set)
2. Environment variables and .env files (fallback)

Security Notes:
- In production, SUPABASE_SERVICE_KEY should NOT be set
- Only SUPABASE_ANON_KEY should be used for user operations
- The service key bypasses RLS policies and is a security risk
"""
import os
import json
import logging
from typing import Optional, List, Dict, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration validation fails."""
    
    def __init__(self, message: str, errors: List[str]):
        self.message = message
        self.errors = errors
        super().__init__(self.message)


def _get_secrets_from_aws(secret_name: str, region: str) -> Dict[str, Any]:
    """
    Retrieve secrets from AWS Secrets Manager.
    
    Args:
        secret_name: Name of the secret in Secrets Manager
        region: AWS region where the secret is stored
        
    Returns:
        Dictionary containing the secret key-value pairs
        
    Raises:
        ConfigurationError: If secret retrieval fails
    """
    import boto3
    from botocore.exceptions import ClientError
    
    try:
        client = boto3.client('secretsmanager', region_name=region)
        response = client.get_secret_value(SecretId=secret_name)
        
        if 'SecretString' in response:
            return json.loads(response['SecretString'])
        else:
            raise ConfigurationError(
                f"Secret {secret_name} does not contain a string value",
                [f"Binary secrets are not supported"]
            )
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_message = e.response.get('Error', {}).get('Message', str(e))
        raise ConfigurationError(
            f"Failed to retrieve secret {secret_name}",
            [f"AWS Error ({error_code}): {error_message}"]
        )
    except json.JSONDecodeError as e:
        raise ConfigurationError(
            f"Secret {secret_name} contains invalid JSON",
            [str(e)]
        )


def _load_configuration() -> tuple[Dict[str, Any], str]:
    """
    Load configuration from the appropriate source.
    
    Priority:
    1. AWS Secrets Manager (if AWS_SECRETS_NAME is set)
    2. Environment variables and .env files
    
    Returns:
        Tuple of (config_dict, source_name)
    """
    aws_secrets_name = os.getenv("AWS_SECRETS_NAME")
    aws_region = os.getenv("AWS_REGION", "us-east-1")
    
    if aws_secrets_name:
        logger.info(f"Loading configuration from AWS Secrets Manager: {aws_secrets_name}")
        secrets = _get_secrets_from_aws(aws_secrets_name, aws_region)
        return secrets, f"AWS Secrets Manager ({aws_secrets_name})"
    else:
        # Load from .env files
        load_dotenv()
        logger.info("Loading configuration from environment variables and .env files")
        return {}, "environment variables/.env files"


# Load configuration at module import time
_config_values, _config_source = _load_configuration()


def _get_config_value(key: str, default: str = "") -> str:
    """
    Get a configuration value from the loaded config or environment.
    
    Args:
        key: Configuration key name
        default: Default value if not found
        
    Returns:
        Configuration value
    """
    # First check if we loaded from Secrets Manager
    if _config_values and key in _config_values:
        return str(_config_values[key])
    # Fall back to environment variables
    return os.getenv(key, default)


class Settings(BaseSettings):
    """Application settings loaded from environment variables or Secrets Manager."""
    
    # Supabase Configuration
    supabase_url: str = _get_config_value("SUPABASE_URL", "")
    supabase_service_key: str = _get_config_value("SUPABASE_SERVICE_KEY", "")
    supabase_anon_key: str = _get_config_value("SUPABASE_ANON_KEY", "")
    
    # AWS Configuration
    aws_region: str = _get_config_value("AWS_REGION", "us-east-1")
    aws_profile: Optional[str] = os.getenv("AWS_PROFILE")
    aws_secrets_name: Optional[str] = os.getenv("AWS_SECRETS_NAME")
    
    # Bedrock Configuration
    bedrock_model_id: str = _get_config_value("BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0")
    
    # API Configuration
    api_host: str = _get_config_value("API_HOST", "0.0.0.0")
    api_port: int = int(_get_config_value("API_PORT", "8000"))
    
    # Environment Configuration
    environment: str = _get_config_value("ENVIRONMENT", "development")
    
    # System User Configuration (for testing)
    system_user_id: str = _get_config_value("SYSTEM_USER_ID", "00000000-0000-0000-0000-000000000000")
    
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
    
    # Configuration source tracking
    _config_source: str = _config_source
    
    @property
    def config_source(self) -> str:
        """Get the source of the configuration."""
        return self._config_source
    
    @property
    def is_using_secrets_manager(self) -> bool:
        """Check if configuration was loaded from Secrets Manager."""
        return self.aws_secrets_name is not None
    
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
                - config_source: Where configuration was loaded from
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
            "config_source": self._config_source,
            "has_service_key": self.has_service_key,
            "has_anon_key": self.has_anon_key,
            "is_valid": is_valid,
            "warnings": warnings,
            "errors": errors
        }
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"  # Ignore extra fields from environment
    )


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
    
    # Log configuration source
    logger.info(f"Configuration source: {config_status['config_source']}")
    
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
        f"config_source={config_status['config_source']}, "
        f"has_anon_key={config_status['has_anon_key']}, "
        f"has_service_key={config_status['has_service_key']}, "
        f"is_valid={config_status['is_valid']}"
    )
