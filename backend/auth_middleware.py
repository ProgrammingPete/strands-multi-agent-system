"""
Authentication middleware for JWT validation.

This module provides JWT validation and user identity extraction
using Supabase Auth. It ensures all database operations respect
Row Level Security policies by validating user tokens.
"""
import os
import logging
from typing import Optional
from supabase import create_client, Client

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """
    Raised when JWT validation fails.
    
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
            "INVALID_TOKEN": "Your session is invalid. Please log in again.",
            "EXPIRED_TOKEN": "Your session has expired. Please log in again.",
            "MISSING_TOKEN": "Authentication required. Please log in.",
            "MALFORMED_TOKEN": "Invalid authentication format. Please log in again.",
            "CONFIGURATION_ERROR": "Server configuration error. Please contact support."
        }
        return messages.get(code, "Authentication error. Please try again.")


def validate_jwt(jwt_token: str) -> str:
    """
    Validate JWT token using Supabase Auth and extract user_id.
    
    This function uses Supabase's auth.get_user() method which:
    - Validates the JWT signature using the project's signing keys
    - Checks that the token hasn't expired
    - Verifies the token was issued by this Supabase project
    - Returns the user object if valid
    
    The auth.get_user() method is the recommended way to validate JWTs
    because it handles all verification logic server-side and validates
    against the project's JWKS (JSON Web Key Set).
    
    Args:
        jwt_token: JWT token from Authorization header
        
    Returns:
        user_id as UUID string (from the 'sub' claim)
        
    Raises:
        AuthenticationError: If token is invalid, expired, or missing
    """
    if not jwt_token:
        raise AuthenticationError(
            "JWT token is required",
            "MISSING_TOKEN"
        )
    
    # Strip 'Bearer ' prefix if present
    if jwt_token.startswith("Bearer "):
        jwt_token = jwt_token[7:]
    
    try:
        # Create Supabase client with pub key for JWT verification
        supabase_url = os.getenv("SUPABASE_URL")
        pub_key = os.getenv("SUPABASE_PUB_KEY")
        
        if not supabase_url:
            raise AuthenticationError(
                "SUPABASE_URL not configured",
                "CONFIGURATION_ERROR"
            )
        
        if not pub_key:
            raise AuthenticationError(
                "SUPABASE_PUB_KEY not configured",
                "CONFIGURATION_ERROR"
            )
        
        # Create client for auth verification
        supabase = create_client(supabase_url, pub_key)
        
        # Verify JWT and get user using Supabase Auth
        # This validates the JWT signature, expiration, and issuer
        user_response = supabase.auth.get_user(jwt_token)
        
        if not user_response or not user_response.user:
            raise AuthenticationError(
                "Invalid JWT token - no user found",
                "INVALID_TOKEN"
            )
        
        # Extract user_id from the user object (corresponds to 'sub' claim)
        user_id = user_response.user.id
        logger.info(f"JWT validated successfully for user {user_id}")
        
        return user_id
        
    except AuthenticationError:
        raise
    except Exception as e:
        error_str = str(e).lower()
        
        # Determine specific error type from exception message
        if "expired" in error_str:
            raise AuthenticationError(
                f"JWT token has expired: {str(e)}",
                "EXPIRED_TOKEN"
            )
        elif "invalid" in error_str or "malformed" in error_str:
            raise AuthenticationError(
                f"JWT token is invalid: {str(e)}",
                "INVALID_TOKEN"
            )
        else:
            logger.error(f"JWT validation failed: {str(e)}")
            raise AuthenticationError(
                f"JWT validation error: {str(e)}",
                "INVALID_TOKEN"
            )


def extract_user_id(jwt_token: str) -> str:
    """
    Extract user_id from validated JWT.
    
    This is a convenience function that validates and extracts in one step.
    Use this when you need the user_id and want to ensure the token is valid.
    
    Args:
        jwt_token: JWT token from Authorization header
        
    Returns:
        user_id as UUID string
        
    Raises:
        AuthenticationError: If token is invalid or expired
    """
    return validate_jwt(jwt_token)
