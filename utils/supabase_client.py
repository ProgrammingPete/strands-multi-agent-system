"""
Supabase client wrapper with error handling and retry logic.

This module provides a robust Supabase client with:
- Automatic retry logic with exponential backoff
- Connection pooling
- Error handling and logging
- Environment-based configuration
"""

import os
import logging
import asyncio
from typing import Optional, TypeVar, Callable, Any
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
            last_exception = None
            
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
        
        Raises:
            SupabaseConnectionError: If required environment variables are missing
                                    or connection fails
        """
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not supabase_url or not supabase_key:
            raise SupabaseConnectionError(
                "Missing required environment variables: SUPABASE_URL and/or SUPABASE_SERVICE_KEY"
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
