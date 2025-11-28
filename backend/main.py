"""
FastAPI backend service for multi-agent chat system.
Provides REST API endpoints for chat streaming and conversation management.
"""
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from contextlib import asynccontextmanager

from backend.config import settings
from backend.models import (
    ChatRequest,
    ConversationCreate,
    ConversationResponse,
    ConversationWithMessages,
    ErrorResponse,
)
from backend.chat_service import ChatService
from backend.conversation_service import ConversationService

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
    logger.info(f"Supabase URL: {settings.supabase_url}")
    logger.info(f"Bedrock Model: {settings.bedrock_model_id}")
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
async def stream_chat(request: ChatRequest):
    """
    Stream chat response using Server-Sent Events.
    
    Performance optimizations (Task 23.2):
    - Disabled all buffering for minimal latency
    - Added streaming-specific headers
    - Optimized for real-time token delivery
    
    Args:
        request: Chat request with message and context
        
    Returns:
        StreamingResponse with SSE format
    """
    logger.info(f"Received chat request for conversation {request.conversation_id}")
    
    return StreamingResponse(
        chat_service.stream_chat_response(request),
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
async def list_conversations(user_id: str, limit: int = 50, offset: int = 0):
    """
    List conversations for a user with pagination support.
    
    Args:
        user_id: User ID
        limit: Maximum number of conversations to return (default: 50)
        offset: Number of conversations to skip for pagination (default: 0)
        
    Returns:
        Object with conversations list and pagination metadata
    """
    try:
        conversations, total_count = await conversation_service.list_conversations(
            user_id, limit, offset
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
async def create_conversation(request: ConversationCreate):
    """
    Create a new conversation.
    
    Args:
        request: Conversation creation request
        
    Returns:
        Created conversation
    """
    try:
        conversation = await conversation_service.create_conversation(request)
        return conversation
    except Exception as e:
        logger.error(f"Error creating conversation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/conversations/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation(
    conversation_id: str, 
    user_id: str,
    message_limit: int = 100,
    message_offset: int = 0
):
    """
    Get a conversation with its messages (paginated).
    
    Args:
        conversation_id: Conversation ID
        user_id: User ID (for authorization)
        message_limit: Maximum number of messages to return (default: 100, max: 500)
        message_offset: Number of messages to skip for pagination (default: 0)
        
    Returns:
        Conversation with messages
    """
    try:
        conversation = await conversation_service.get_conversation(
            conversation_id, user_id, message_limit, message_offset
        )
        return conversation
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting conversation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, user_id: str):
    """
    Delete a conversation and its messages.
    
    Args:
        conversation_id: Conversation ID
        user_id: User ID (for authorization)
        
    Returns:
        Success message
    """
    try:
        await conversation_service.delete_conversation(conversation_id, user_id)
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
