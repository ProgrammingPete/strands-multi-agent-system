"""
Admin authentication module for privileged operations.

This module provides authentication for admin-only operations that require
the service key (which bypasses RLS). Admin operations should be rare and
carefully controlled.

Security Notes:
- Admin credentials are separate from regular user authentication
- Service key usage is logged for audit purposes
- In production, admin operations require explicit credential validation
"""
import os
import logging
import hashlib
import secrets
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class AdminAuthenticationError(Exception):
    """Raised when admin authentication fails."""
    
    def __init__(self, message: str, code: str):
        self.message = message
        self.code = code
        super().__init__(self.message)


class AdminAuthenticator:
    """
    Handles authentication for admin-only operations.
    
    Admin operations are those that require the service key, which bypasses
    RLS policies. These should be rare and carefully controlled.
    """
    
    def __init__(self):
        """Initialize the admin authenticator."""
        self._admin_api_key = os.getenv("ADMIN_API_KEY")
        self._environment = os.getenv("ENVIRONMENT", "development")
    
    @property
    def is_configured(self) -> bool:
        """Check if admin authentication is configured."""
        return bool(self._admin_api_key)
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self._environment.lower() == "production"
    
    def validate_admin_credentials(
        self,
        api_key: str,
        operation: str,
        resource: Optional[str] = None
    ) -> bool:
        """
        Validate admin credentials before allowing privileged operations.
        
        This method validates the provided API key against the configured
        admin key and logs the operation for audit purposes.
        
        Args:
            api_key: The admin API key provided by the caller
            operation: Description of the operation being performed
            resource: Optional resource identifier being accessed
            
        Returns:
            True if credentials are valid
            
        Raises:
            AdminAuthenticationError: If credentials are invalid or not configured
        """
        # Log the admin operation attempt
        logger.info(
            f"Admin operation attempted: operation={operation}, "
            f"resource={resource}, timestamp={datetime.utcnow().isoformat()}"
        )
        
        # In development without admin key configured, allow with warning
        if not self._admin_api_key:
            if self.is_production:
                logger.error("Admin operation denied: ADMIN_API_KEY not configured in production")
                raise AdminAuthenticationError(
                    "Admin API key not configured",
                    "ADMIN_NOT_CONFIGURED"
                )
            else:
                logger.warning(
                    f"Admin operation allowed without key in {self._environment} mode: {operation}"
                )
                return True
        
        # Validate the API key using constant-time comparison
        if not api_key:
            logger.warning(f"Admin operation denied: No API key provided for {operation}")
            raise AdminAuthenticationError(
                "Admin API key required",
                "ADMIN_KEY_REQUIRED"
            )
        
        # Use constant-time comparison to prevent timing attacks
        if not secrets.compare_digest(api_key, self._admin_api_key):
            logger.warning(
                f"Admin operation denied: Invalid API key for {operation}"
            )
            raise AdminAuthenticationError(
                "Invalid admin API key",
                "INVALID_ADMIN_KEY"
            )
        
        # Log successful authentication
        logger.info(
            f"Admin operation authorized: operation={operation}, "
            f"resource={resource}, timestamp={datetime.utcnow().isoformat()}"
        )
        
        return True
    
    def get_service_key_client(
        self,
        api_key: str,
        operation: str,
        resource: Optional[str] = None
    ):
        """
        Get a Supabase client with service key after validating admin credentials.
        
        This method validates admin credentials and returns a service key client
        that bypasses RLS. Use with extreme caution.
        
        Args:
            api_key: The admin API key
            operation: Description of the operation
            resource: Optional resource identifier
            
        Returns:
            Supabase client with service key
            
        Raises:
            AdminAuthenticationError: If credentials are invalid
            SupabaseConnectionError: If service key is not configured
        """
        from utils.supabase_client import get_supabase_client, SupabaseConnectionError
        
        # Validate admin credentials first
        self.validate_admin_credentials(api_key, operation, resource)
        
        # Get the service key client
        client_wrapper = get_supabase_client()
        
        # Verify service key is available
        service_key = os.getenv("SUPABASE_SERVICE_KEY")
        if not service_key:
            raise SupabaseConnectionError(
                "SUPABASE_SERVICE_KEY not configured - admin operations unavailable"
            )
        
        # Log that service key is being used
        logger.warning(
            f"Service key client created for admin operation: {operation}. "
            "RLS policies will be bypassed."
        )
        
        return client_wrapper.client


# Global instance
_admin_authenticator: Optional[AdminAuthenticator] = None


def get_admin_authenticator() -> AdminAuthenticator:
    """Get the global admin authenticator instance."""
    global _admin_authenticator
    if _admin_authenticator is None:
        _admin_authenticator = AdminAuthenticator()
    return _admin_authenticator


def validate_admin_operation(
    api_key: str,
    operation: str,
    resource: Optional[str] = None
) -> bool:
    """
    Convenience function to validate admin credentials.
    
    Args:
        api_key: The admin API key
        operation: Description of the operation
        resource: Optional resource identifier
        
    Returns:
        True if credentials are valid
        
    Raises:
        AdminAuthenticationError: If credentials are invalid
    """
    return get_admin_authenticator().validate_admin_credentials(
        api_key, operation, resource
    )
