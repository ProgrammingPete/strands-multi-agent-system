"""
Pydantic models for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from enum import Enum


class AgentType(str, Enum):
    """Enum for different agent types."""
    SUPERVISOR = "supervisor"
    INVOICES = "invoices"
    APPOINTMENTS = "appointments"
    PROJECTS = "projects"
    PROPOSALS = "proposals"
    CONTACTS = "contacts"
    REVIEWS = "reviews"
    CAMPAIGNS = "campaigns"
    TASKS = "tasks"
    SETTINGS = "settings"


class Message(BaseModel):
    """Message model for conversation history."""
    id: str
    content: str
    role: Literal["user", "assistant"]
    timestamp: datetime
    agent_type: Optional[AgentType] = None
    metadata: Optional[Dict[str, Any]] = None


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., min_length=1, max_length=10000)
    conversation_id: str
    user_id: str
    history: List[Message] = Field(default_factory=list)


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    message: Message
    agent_type: AgentType
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)


class StreamChunk(BaseModel):
    """Model for streaming response chunks."""
    type: Literal["token", "tool_call", "complete", "error"]
    content: Optional[str] = None
    tool_call: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    agent_type: Optional[AgentType] = None


class ConversationCreate(BaseModel):
    """Request model for creating a conversation."""
    user_id: str
    title: Optional[str] = None


class ConversationResponse(BaseModel):
    """Response model for conversation data."""
    id: str
    user_id: str
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_message_at: Optional[datetime] = None
    message_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationWithMessages(ConversationResponse):
    """Conversation response with messages included."""
    messages: List[Message] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    """Error response model."""
    error: Dict[str, Any] = Field(
        ...,
        example={
            "code": "INTERNAL_ERROR",
            "message": "An error occurred",
            "userMessage": "Something went wrong. Please try again.",
            "suggestedActions": ["Retry the request", "Contact support"],
            "retryable": True
        }
    )
