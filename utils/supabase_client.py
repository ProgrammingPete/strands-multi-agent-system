"""
Supabase client wrapper with error handling and retry logic.

This module provides a robust Supabase client with:
- Automatic retry logic with exponential backoff
- Connection pooling
- Error handling and logging
- Environment-based configuration
- User-scoped client creation for RLS enforcement
"""

import os
import logging
from typing import Optional, TypeVar, Callable, Any, Dict, List
from functools import wraps
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Type variable for generic retry function
T = TypeVar('T')


class SupabaseClientError(Exception):
    """Base exception for Supabase client errors."""
    pass


class SupabaseConnectionError(SupabaseClientError):
    """Exception raised when connection to Supabase fails."""
    pass


class SupabaseQueryError(SupabaseClientError):
    """Exception raised when a query fails."""
    pass


def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    exponential_base: int = 2
):
    """
    Decorator to retry a function with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff calculation
    
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception: Optional[Exception] = None 
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_attempts - 1:
                        delay = min(base_delay * (exponential_base ** attempt), max_delay)
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed: {str(e)}. "
                            f"Retrying in {delay:.2f} seconds..."
                        )
                        import time
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed. Last error: {str(e)}"
                        )
            
            if last_exception is None:
                raise RuntimeError("Operation failed after retries, but no exception was captured.")
            raise last_exception
        
        return wrapper
    return decorator


class SupabaseClientWrapper:
    """
    Wrapper for Supabase client with enhanced error handling and retry logic.
    
    This class provides a singleton pattern for the Supabase client and includes
    automatic retry logic for failed operations.
    """
    
    _instance: Optional['SupabaseClientWrapper'] = None
    _client: Optional[Client] = None
    
    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the Supabase client wrapper."""
        if self._client is None:
            self._initialize_client()
    
    def _initialize_client(self):
        """
        Initialize the Supabase client with configuration from environment variables.
        
        In production, uses SUPABASE_ANON_KEY (respects RLS).
        In development, prefers SUPABASE_SERVICE_KEY if available, falls back to anon key.
        
        Raises:
            SupabaseConnectionError: If required environment variables are missing
                                    or connection fails
        """
        supabase_url = os.getenv("SUPABASE_URL")
        environment = os.getenv("ENVIRONMENT", "development")
        
        # In production, prefer anon key (respects RLS)
        # In development, prefer secret key if available (for admin operations)
        if environment == "production":
            supabase_key = os.getenv("SUPABASE_ANON_KEY")
            if not supabase_key:
                supabase_key = os.getenv("SUPABASE_SECRET_KEY")
            logger.info(f"Production mode: using {'anon' if supabase_key == os.getenv('SUPABASE_ANON_KEY') else 'secret'} key")
        else:
            supabase_key = os.getenv("SUPABASE_SECRET_KEY") or os.getenv("SUPABASE_ANON_KEY")
            logger.info(f"Development mode: using {'secret' if supabase_key == os.getenv('SUPABASE_SECRET_KEY') else 'anon'} key")
        
        if not supabase_url or not supabase_key:
            raise SupabaseConnectionError(
                "Missing required environment variables: SUPABASE_URL and/or SUPABASE_ANON_KEY"
            )
        
        try:
            # Create client without custom options first
            # The schema will be set to 'api' via table queries
            self._client = create_client(
                supabase_url=supabase_url,
                supabase_key=supabase_key
            )
            
            logger.info("Supabase client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {str(e)}")
            raise SupabaseConnectionError(f"Failed to connect to Supabase: {str(e)}")
    
    @property
    def client(self) -> Client:
        """
        Get the Supabase client instance.
        
        Returns:
            Supabase client instance
        
        Raises:
            SupabaseConnectionError: If client is not initialized
        """
        if self._client is None:
            raise SupabaseConnectionError("Supabase client not initialized")
        return self._client
    
    @retry_with_backoff(max_attempts=3, base_delay=1.0, max_delay=10.0)
    def execute_query(self, query_func: Callable[[], Any]) -> Any:
        """
        Execute a Supabase query with automatic retry logic.
        
        Args:
            query_func: Function that executes the query
        
        Returns:
            Query result
        
        Raises:
            SupabaseQueryError: If query fails after all retries
        """
        try:
            result = query_func()
            return result
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise SupabaseQueryError(f"Query failed: {str(e)}")
    
    def table(self, table_name: str):
        """
        Get a table reference for querying.
        
        Args:
            table_name: Name of the table
        
        Returns:
            Table reference
        """
        return self.client.schema("api").table(table_name)
    
    def health_check(self) -> bool:
        """
        Perform a health check on the Supabase connection.
        
        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            # Try a simple query to verify connection
            self.client.schema("api").table('agent_conversations').select('id').limit(1).execute()
            logger.info("Supabase health check passed")
            return True
        except Exception as e:
            logger.error(f"Supabase health check failed: {str(e)}")
            return False
    
    def create_user_scoped_client(self, user_jwt: str) -> Client:
        """
        Create a Supabase client scoped to a specific user.
        
        This client respects RLS policies by using the anon key with
        the user's JWT token in the Authorization header. All queries
        made with this client will be filtered by RLS policies.
        
        Args:
            user_jwt: User's JWT token (without 'Bearer ' prefix)
            
        Returns:
            Supabase client configured with user JWT and anon key
            
        Raises:
            SupabaseConnectionError: If SUPABASE_ANON_KEY is not configured
        """
        supabase_url = os.getenv("SUPABASE_URL")
        anon_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not supabase_url:
            raise SupabaseConnectionError("SUPABASE_URL not configured")
        
        if not anon_key:
            raise SupabaseConnectionError(
                "SUPABASE_ANON_KEY not configured - user-scoped operations unavailable"
            )
        
        # Strip 'Bearer ' prefix if present
        if user_jwt.startswith("Bearer "):
            user_jwt = user_jwt[7:]
        
        # Create base client with anon key
        client = create_client(
            supabase_url=supabase_url,
            supabase_key=anon_key
        )
        
        # Override the authorization header to use user's JWT
        # This makes PostgREST treat requests as coming from that user
        client.postgrest.auth(user_jwt)
        
        logger.debug("Created user-scoped Supabase client")
        return client
    
    def verify_key_configuration(self) -> Dict[str, Any]:
        """
        Verify Supabase key configuration on startup.
        
        Logs warnings if using secret key in production or if
        anon key is not configured for user-scoped operations.
        
        Returns:
            dict with:
                - key_type: 'service_key' or 'anon_key'
                - has_anon_key: bool indicating if anon key is available
                - is_valid: bool indicating if configuration is valid
                - warnings: list of warning messages
        """
        secret_key = os.getenv("SUPABASE_SECRET_KEY")
        anon_key = os.getenv("SUPABASE_ANON_KEY")
        environment = os.getenv("ENVIRONMENT", "development")
        
        warnings: List[str] = []
        
        # Check for secret key in production
        if secret_key and environment == "production":
            warning_msg = "WARNING: SUPABASE_SECRET_KEY is set in production - RLS will be bypassed for secret key operations"
            warnings.append(warning_msg)
            logger.warning(warning_msg)
        
        # Check for missing anon key
        if not anon_key:
            warning_msg = "WARNING: SUPABASE_ANON_KEY not configured - user-scoped operations unavailable"
            warnings.append(warning_msg)
            logger.warning(warning_msg)
        
        # Log if using secret key (RLS bypass)
        if secret_key:
            logger.info("Secret key configured - RLS will be bypassed for secret key client")
        
        # Determine key type being used by default client
        key_type = "secret_key" if secret_key else "anon_key"
        
        return {
            "key_type": key_type,
            "has_anon_key": bool(anon_key),
            "is_valid": bool(anon_key),  # Valid if anon key is available for user operations
            "warnings": warnings,
            "environment": environment
        }
    
    def get_admin_client(
        self,
        admin_api_key: str,
        operation: str,
        resource: Optional[str] = None
    ) -> Client:
        """
        Get a Supabase client with secret key for admin operations.
        
        This method validates admin credentials before returning a secret key
        client that bypasses RLS. Use with extreme caution and only for
        legitimate admin operations.
        
        Args:
            admin_api_key: The admin API key for authentication
            operation: Description of the admin operation being performed
            resource: Optional resource identifier being accessed
            
        Returns:
            Supabase client with secret key (bypasses RLS)
            
        Raises:
            AdminAuthenticationError: If admin credentials are invalid
            SupabaseConnectionError: If secret key is not configured
        """
        from backend.admin_auth import validate_admin_operation, AdminAuthenticationError
        
        # Validate admin credentials first
        validate_admin_operation(admin_api_key, operation, resource)
        
        # Verify secret key is available
        secret_key = os.getenv("SUPABASE_SECRET_KEY")
        if not secret_key:
            raise SupabaseConnectionError(
                "SUPABASE_SECRET_KEY not configured - admin operations unavailable"
            )
        
        # Log that secret key is being used for admin operation
        logger.warning(
            f"Admin client created for operation: {operation}. "
            "RLS policies will be bypassed."
        )
        
        # Return the secret key client
        return create_client(
            supabase_url=str(os.getenv("SUPABASE_URL")),
            supabase_key=secret_key
        )


# Global instance
_supabase_wrapper: Optional[SupabaseClientWrapper] = None


def get_supabase_client() -> SupabaseClientWrapper:
    """
    Get the global Supabase client wrapper instance.
    
    Returns:
        SupabaseClientWrapper instance
    """
    global _supabase_wrapper
    if _supabase_wrapper is None:
        _supabase_wrapper = SupabaseClientWrapper()
    return _supabase_wrapper


# Convenience function for direct client access
def get_client() -> Client:
    """
    Get the raw Supabase client instance.
    
    Returns:
        Supabase Client instance
    """
    return get_supabase_client().client
