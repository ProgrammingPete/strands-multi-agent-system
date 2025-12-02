"""
Shared utilities for agent tools.

This module provides common functionality used across all agent tools,
including authentication error handling and client creation logic.
"""

import logging
import os
from typing import Optional, Tuple, Union
import sys

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.supabase_client import get_supabase_client, SupabaseConnectionError, SupabaseClientWrapper
from supabase import Client

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """
    Raised when authentication fails for agent tool operations.
    
    Attributes:
        message: Technical error message for logging
        code: Error code for programmatic handling
        user_message: User-friendly error message for display
    """
    
    def __init__(self, message: str, code: str):
        self.message = message
        self.code = code
        self.user_message = self._get_user_message(code)
        super().__init__(self.message)
        
    def _get_user_message(self, code: str) -> str:
        """Get user-friendly error message based on error code."""
        messages = {
            "MISSING_TOKEN": "Authentication required. Please log in.",
            "MISSING_USER_ID": "User identification required.",
        }
        return messages.get(code, "Authentication error. Please try again.")


def get_supabase_client_for_operation(
    user_id: str, 
    user_jwt: Optional[str] = None
) -> Tuple[Union[Client, SupabaseClientWrapper], bool]:
    """
    Get the appropriate Supabase client based on environment and JWT availability.
    
    In production mode, JWT is required and a user-scoped client is created.
    In development mode, service key fallback is allowed with a warning.
    
    Args:
        user_id: The user ID for the operation (required)
        user_jwt: Optional JWT token for user-scoped client creation
        
    Returns:
        Tuple of (client, is_user_scoped) where:
            - client: Supabase client (either user-scoped or service key wrapper)
            - is_user_scoped: True if using user-scoped client with RLS
            
    Raises:
        AuthenticationError: If JWT is required but not provided (production mode)
    """
    environment = os.getenv("ENVIRONMENT", "development")
    supabase_wrapper = get_supabase_client()
    
    if user_jwt:
        # Production path: Use user-scoped client with RLS enforcement
        try:
            client = supabase_wrapper.create_user_scoped_client(user_jwt)
            logger.debug(f"Using user-scoped client for user {user_id}")
            return client, True
        except SupabaseConnectionError as e:
            logger.error(f"Failed to create user-scoped client: {str(e)}")
            if environment == "production":
                raise AuthenticationError(
                    f"Failed to create user-scoped client: {str(e)}",
                    "MISSING_TOKEN"
                )
            # Fall through to development fallback
            logger.warning("Falling back to service key client in development mode")
    
    if environment == "production":
        # Production without JWT: Fail securely
        raise AuthenticationError(
            "JWT required in production environment",
            "MISSING_TOKEN"
        )
    
    # Development path: Use service key (bypasses RLS)
    logger.warning(f"Using service key - RLS bypassed (development mode) for user {user_id}")
    return supabase_wrapper, False
