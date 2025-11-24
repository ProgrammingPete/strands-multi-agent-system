"""
Error handling utilities for the backend service.
Includes retry logic with exponential backoff and user-friendly error translation.
"""
import asyncio
import logging
from typing import TypeVar, Callable, Any
from backend.config import settings

logger = logging.getLogger(__name__)

T = TypeVar('T')


async def retry_with_backoff(
    func: Callable[[], T],
    max_attempts: int = None,
    base_delay: float = None,
    max_delay: float = None
) -> T:
    """
    Retry a function with exponential backoff.
    
    Args:
        func: The async function to retry
        max_attempts: Maximum number of attempts (default from settings)
        base_delay: Initial delay in seconds (default from settings)
        max_delay: Maximum delay in seconds (default from settings)
    
    Returns:
        The result of the function
    
    Raises:
        The last exception if all attempts fail
    """
    max_attempts = max_attempts or settings.max_retry_attempts
    base_delay = base_delay or settings.base_retry_delay
    max_delay = max_delay or settings.max_retry_delay
    
    last_exception = None
    
    for attempt in range(max_attempts):
        try:
            logger.info(f"Attempt {attempt + 1}/{max_attempts}")
            return await func()
        except Exception as e:
            last_exception = e
            logger.warning(f"Attempt {attempt + 1} failed: {e}")
            
            if attempt < max_attempts - 1:
                delay = min(base_delay * (2 ** attempt), max_delay)
                logger.info(f"Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
    
    logger.error(f"All {max_attempts} attempts failed")
    raise last_exception


def translate_error_to_user_message(error: Exception) -> str:
    """
    Translate technical errors into user-friendly messages.
    
    Args:
        error: The exception to translate
        
    Returns:
        User-friendly error message
    """
    error_str = str(error).lower()
    
    # Network errors
    if "connection" in error_str or "timeout" in error_str:
        return "Unable to connect to the service. Please check your internet connection and try again."
    
    # Authentication errors
    if "auth" in error_str or "unauthorized" in error_str or "forbidden" in error_str:
        return "Authentication failed. Please log in again."
    
    # Rate limiting
    if "rate limit" in error_str or "too many requests" in error_str:
        return "Too many requests. Please wait a moment and try again."
    
    # LLM errors
    if "bedrock" in error_str or "model" in error_str:
        return "The AI service is temporarily unavailable. Please try again in a moment."
    
    # Token limit errors
    if "token" in error_str and "limit" in error_str:
        return "Your message is too long. Please try a shorter message."
    
    # Database errors
    if "supabase" in error_str or "database" in error_str:
        return "Unable to access your data. Please try again."
    
    # Validation errors
    if "validation" in error_str or "invalid" in error_str:
        return "Invalid input. Please check your message and try again."
    
    # Generic error
    return "An unexpected error occurred. Please try again."


def get_error_response(
    error: Exception,
    code: str = "INTERNAL_ERROR",
    retryable: bool = True
) -> dict[str, Any]:
    """
    Create a standardized error response.
    
    Args:
        error: The exception
        code: Error code
        retryable: Whether the error is retryable
        
    Returns:
        Error response dictionary
    """
    user_message = translate_error_to_user_message(error)
    
    return {
        "error": {
            "code": code,
            "message": str(error),
            "userMessage": user_message,
            "suggestedActions": _get_suggested_actions(error),
            "retryable": retryable,
        }
    }


def _get_suggested_actions(error: Exception) -> list[str]:
    """
    Get suggested actions based on error type.
    
    Args:
        error: The exception
        
    Returns:
        List of suggested actions
    """
    error_str = str(error).lower()
    
    if "connection" in error_str or "timeout" in error_str:
        return [
            "Check your internet connection",
            "Try again in a moment",
            "Contact support if the problem persists"
        ]
    
    if "auth" in error_str:
        return [
            "Log in again",
            "Check your credentials",
            "Contact support if you continue to have issues"
        ]
    
    if "rate limit" in error_str:
        return [
            "Wait a moment before trying again",
            "Reduce the frequency of your requests"
        ]
    
    if "token" in error_str and "limit" in error_str:
        return [
            "Try a shorter message",
            "Break your request into smaller parts"
        ]
    
    return [
        "Try again",
        "Contact support if the problem persists"
    ]
