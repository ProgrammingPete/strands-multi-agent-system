"""
FastAPI backend service for multi-agent chat system.
Provides REST API endpoints for chat streaming and conversation management.
"""
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from contextlib import asynccontextmanager

from backend.config import settings, validate_startup_configuration, ConfigurationError
from backend.models import (
    ChatRequest,
    ConversationCreate,
    ConversationResponse,
    ConversationWithMessages,
    ErrorResponse,
)
from backend.chat_service import ChatService
from backend.conversation_service import ConversationService
from backend.auth_middleware import validate_jwt, AuthenticationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Initialize services
chat_service = ChatService()
conversation_service = ConversationService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("Starting FastAPI backend service")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Supabase URL: {settings.supabase_url}")
    logger.info(f"Bedrock Model: {settings.bedrock_model_id}")
    
    # Validate configuration for the current environment
    # This will raise ConfigurationError in production if config is invalid
    try:
        validate_startup_configuration()
        logger.info("Configuration validation passed")
    except ConfigurationError as e:
        logger.critical(f"Configuration validation failed: {e.message}")
        for error in e.errors:
            logger.critical(f"  - {error}")
        raise
    
    yield
    # Shutdown
    logger.info("Shutting down FastAPI backend service")


# Create FastAPI app
app = FastAPI(
    title="Canvalo Multi-Agent Chat API",
    description="Backend API for multi-agent chat system with specialized business domain agents",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests and responses."""
    logger.info(f"Request: {request.method} {request.url.path}")
    try:
        response = await call_next(request)
        logger.info(f"Response: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Request failed: {e}", exc_info=True)
        raise


@app.get("/")
async def root():
    """Root endpoint - health check."""
    return {
        "status": "ok",
        "service": "Canvalo Multi-Agent Chat API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "supabase_configured": bool(settings.supabase_url),
        "bedrock_model": settings.bedrock_model_id,
    }


@app.post("/api/chat/stream")
async def stream_chat(
    request: ChatRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Stream chat response using Server-Sent Events with JWT authentication.
    
    Performance optimizations (Task 23.2):
    - Disabled all buffering for minimal latency
    - Added streaming-specific headers
    - Optimized for real-time token delivery
    
    Security (Task 5.1):
    - JWT validation before processing requests
    - User ID verification against JWT claims
    - Appropriate HTTP errors for auth failures
    
    Args:
        request: Chat request with message and context
        authorization: Bearer token from Authorization header
        
    Returns:
        StreamingResponse with SSE format
        
    Raises:
        HTTPException 401: Missing or invalid authorization header
        HTTPException 403: User ID mismatch between request and JWT
    """
    logger.info(f"Received chat request for conversation {request.conversation_id}")
    
    # Extract and validate JWT token
    jwt_token = None
    validated_user_id = None
    
    if authorization:
        # Extract JWT from Authorization header
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail={
                    "code": "MALFORMED_TOKEN",
                    "message": "Authorization header must use Bearer scheme",
                    "userMessage": "Invalid authentication format. Please log in again."
                }
            )
        
        jwt_token = authorization.replace("Bearer ", "")
        
        try:
            # Validate JWT and extract user_id
            validated_user_id = validate_jwt(jwt_token)
        except AuthenticationError as e:
            raise HTTPException(
                status_code=401,
                detail={
                    "code": e.code,
                    "message": e.message,
                    "userMessage": e.user_message
                }
            )
        
        # Verify user_id in request matches JWT
        if request.user_id != validated_user_id:
            logger.warning(
                f"User ID mismatch: request={request.user_id}, jwt={validated_user_id}"
            )
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "USER_ID_MISMATCH",
                    "message": "User ID in request does not match authenticated user",
                    "userMessage": "You are not authorized to perform this action."
                }
            )
    else:
        # Check environment - in production, JWT is required
        environment = settings.environment if hasattr(settings, 'environment') else "development"
        if environment == "production":
            raise HTTPException(
                status_code=401,
                detail={
                    "code": "MISSING_TOKEN",
                    "message": "Authorization header is required",
                    "userMessage": "Authentication required. Please log in."
                }
            )
        else:
            # Development mode: allow requests without JWT (with warning)
            logger.warning(
                f"Request without JWT in {environment} mode - RLS may be bypassed"
            )
    
    return StreamingResponse(
        chat_service.stream_chat_response(request, jwt_token),
        media_type="text/event-stream",
        headers={
            # Disable all caching for real-time streaming
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            # Keep connection alive for streaming
            "Connection": "keep-alive",
            # Disable buffering at various proxy levels
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "X-Content-Type-Options": "nosniff",
            # Hint to proxies that this is a streaming response
            "Transfer-Encoding": "chunked",
        }
    )


@app.get("/api/conversations")
async def list_conversations(
    user_id: str,
    limit: int = 50,
    offset: int = 0,
    authorization: Optional[str] = Header(None)
):
    """
    List conversations for a user with pagination support.
    
    Args:
        user_id: User ID
        limit: Maximum number of conversations to return (default: 50)
        offset: Number of conversations to skip for pagination (default: 0)
        authorization: Bearer token from Authorization header
        
    Returns:
        Object with conversations list and pagination metadata
    """
    # Extract JWT token for user-scoped operations
    jwt_token = None
    if authorization and authorization.startswith("Bearer "):
        jwt_token = authorization.replace("Bearer ", "")
    
    try:
        conversations, total_count = await conversation_service.list_conversations(
            user_id, limit, offset, jwt_token
        )
        return {
            "conversations": conversations,
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(conversations) < total_count
        }
    except Exception as e:
        logger.error(f"Error listing conversations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/conversations", response_model=ConversationResponse)
async def create_conversation(
    request: ConversationCreate,
    authorization: Optional[str] = Header(None)
):
    """
    Create a new conversation.
    
    Args:
        request: Conversation creation request
        authorization: Bearer token from Authorization header
        
    Returns:
        Created conversation
    """
    # Extract JWT token for user-scoped operations
    jwt_token = None
    if authorization and authorization.startswith("Bearer "):
        jwt_token = authorization.replace("Bearer ", "")
    
    try:
        conversation = await conversation_service.create_conversation(request, jwt_token)
        return conversation
    except Exception as e:
        logger.error(f"Error creating conversation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/conversations/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation(
    conversation_id: str, 
    user_id: str,
    message_limit: int = 100,
    message_offset: int = 0,
    authorization: Optional[str] = Header(None)
):
    """
    Get a conversation with its messages (paginated).
    
    Args:
        conversation_id: Conversation ID
        user_id: User ID (for authorization)
        message_limit: Maximum number of messages to return (default: 100, max: 500)
        message_offset: Number of messages to skip for pagination (default: 0)
        authorization: Bearer token from Authorization header
        
    Returns:
        Conversation with messages
    """
    # Extract JWT token for user-scoped operations
    jwt_token = None
    if authorization and authorization.startswith("Bearer "):
        jwt_token = authorization.replace("Bearer ", "")
    
    try:
        conversation = await conversation_service.get_conversation(
            conversation_id, user_id, message_limit, message_offset, jwt_token
        )
        return conversation
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting conversation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    user_id: str,
    authorization: Optional[str] = Header(None)
):
    """
    Delete a conversation and its messages.
    
    Args:
        conversation_id: Conversation ID
        authorization: Bearer token from Authorization header
        user_id: User ID (for authorization)
        
    Returns:
        Success message
    """
    # Extract JWT token for user-scoped operations
    jwt_token = None
    if authorization and authorization.startswith("Bearer "):
        jwt_token = authorization.replace("Bearer ", "")
    
    try:
        await conversation_service.delete_conversation(conversation_id, user_id, jwt_token)
        return {"status": "deleted", "conversation_id": conversation_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with user-friendly messages."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": str(exc.detail),
                "userMessage": exc.detail,
                "retryable": exc.status_code >= 500,
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with user-friendly messages."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(exc),
                "userMessage": "An unexpected error occurred. Please try again.",
                "retryable": True,
            }
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level="info"
    )
