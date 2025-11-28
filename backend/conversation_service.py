"""
Conversation service for managing conversations and messages in Supabase.

Performance optimizations (Task 23.1):
- Optimized queries with proper column selection
- Pagination support for large message histories
- Efficient message loading with limit/offset
- Batch operations for bulk message retrieval
"""
import logging
from typing import List, Optional, Tuple
from datetime import datetime

from utils.supabase_client import get_supabase_client
from backend.models import (
    ConversationCreate,
    ConversationResponse,
    ConversationWithMessages,
    Message,
)

logger = logging.getLogger(__name__)

# Default limits for query optimization
DEFAULT_CONVERSATION_LIMIT = 50
DEFAULT_MESSAGE_LIMIT = 100
MAX_MESSAGE_LIMIT = 500


class ConversationService:
    """Service for managing conversations and messages with optimized queries."""
    
    def __init__(self):
        """Initialize the conversation service."""
        try:
            self.supabase = get_supabase_client()
            logger.info("ConversationService initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Supabase client: {e}")
            logger.warning("Conversation service will not be available")
            self.supabase = None
    
    async def list_conversations(
        self,
        user_id: str,
        limit: int = DEFAULT_CONVERSATION_LIMIT,
        offset: int = 0
    ) -> Tuple[List[ConversationResponse], int]:
        """
        List conversations for a user with pagination support.
        
        Optimized query: Uses idx_agent_conversations_user index
        for efficient user_id + updated_at ordering.
        
        Args:
            user_id: User ID
            limit: Maximum number of conversations to return
            offset: Number of conversations to skip (for pagination)
            
        Returns:
            Tuple of (list of conversations, total count)
        """
        if not self.supabase:
            raise RuntimeError("Supabase client not initialized")
        
        try:
            logger.info(f"Listing conversations for user {user_id} (limit={limit}, offset={offset})")
            
            if not user_id:
                raise ValueError("User ID is required")
            
            # Optimized query: select only needed columns for listing
            # Uses idx_agent_conversations_user index
            response = (
                self.supabase.table("agent_conversations")
                .select("id, user_id, title, created_at, updated_at, last_message_at, message_count, metadata", count="exact")
                .eq("user_id", user_id)
                .order("updated_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )
            
            conversations = [
                ConversationResponse(**conv) for conv in response.data
            ]
            
            total_count = response.count if response.count is not None else len(conversations)
            
            logger.info(f"Found {len(conversations)} conversations (total: {total_count})")
            return conversations, total_count
            
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error listing conversations: {e}", exc_info=True)
            raise RuntimeError(f"Failed to list conversations: {str(e)}")
    
    async def create_conversation(
        self,
        request: ConversationCreate
    ) -> ConversationResponse:
        """
        Create a new conversation.
        
        Args:
            request: Conversation creation request
            
        Returns:
            Created conversation
        """
        if not self.supabase:
            raise RuntimeError("Supabase client not initialized")
        
        try:
            logger.info(f"Creating conversation for user {request.user_id}")
            
            data = {
                "user_id": request.user_id,
                "title": request.title,
                "metadata": {},
            }
            
            response = (
                self.supabase.table("agent_conversations")
                .insert(data)
                .execute()
            )
            
            conversation = ConversationResponse(**response.data[0])
            logger.info(f"Created conversation {conversation.id}")
            return conversation
            
        except Exception as e:
            logger.error(f"Error creating conversation: {e}", exc_info=True)
            raise
    
    async def get_conversation(
        self,
        conversation_id: str,
        user_id: str,
        message_limit: int = DEFAULT_MESSAGE_LIMIT,
        message_offset: int = 0
    ) -> ConversationWithMessages:
        """
        Get a conversation with its messages (paginated).
        
        Optimized query: Uses idx_agent_messages_conversation_covering
        for efficient message retrieval with index-only scans.
        
        Args:
            conversation_id: Conversation ID
            user_id: User ID (for authorization)
            message_limit: Maximum number of messages to return
            message_offset: Number of messages to skip (for pagination)
            
        Returns:
            Conversation with messages
        """
        if not self.supabase:
            raise RuntimeError("Supabase client not initialized")
        
        try:
            logger.info(f"Getting conversation {conversation_id} (msg_limit={message_limit})")
            
            # Enforce maximum limit to prevent memory issues
            message_limit = min(message_limit, MAX_MESSAGE_LIMIT)
            
            # Get conversation (don't use single() to avoid error when not found)
            conv_response = (
                self.supabase.table("agent_conversations")
                .select("id, user_id, title, created_at, updated_at, last_message_at, message_count, metadata")
                .eq("id", conversation_id)
                .eq("user_id", user_id)
                .execute()
            )
            
            if not conv_response or not conv_response.data or len(conv_response.data) == 0:
                raise ValueError(f"Conversation {conversation_id} not found")
            
            # Get the first (and should be only) result
            conv_data = conv_response.data[0]
            
            # Optimized message query: select only needed columns
            # Uses idx_agent_messages_conversation_covering for index-only scan
            msg_response = (
                self.supabase.table("agent_messages")
                .select("id, content, role, agent_type, metadata, created_at")
                .eq("conversation_id", conversation_id)
                .order("created_at", desc=False)
                .range(message_offset, message_offset + message_limit - 1)
                .execute()
            )
            
            messages = [
                Message(
                    id=msg["id"],
                    content=msg["content"],
                    role=msg["role"],
                    timestamp=datetime.fromisoformat(msg["created_at"].replace("Z", "+00:00")),
                    agent_type=msg.get("agent_type"),
                    metadata=msg.get("metadata", {}),
                )
                for msg in msg_response.data
            ]
            
            conversation = ConversationWithMessages(
                **conv_data,
                messages=messages
            )
            
            logger.info(f"Found conversation with {len(messages)} messages")
            return conversation
            
        except Exception as e:
            logger.error(f"Error getting conversation: {e}", exc_info=True)
            raise
    
    async def get_recent_messages(
        self,
        conversation_id: str,
        limit: int = 10
    ) -> List[Message]:
        """
        Get the most recent messages from a conversation.
        
        Optimized for context building - uses idx_agent_messages_conversation_recent
        for efficient retrieval of recent messages.
        
        Args:
            conversation_id: Conversation ID
            limit: Maximum number of messages to return
            
        Returns:
            List of recent messages (most recent first)
        """
        if not self.supabase:
            raise RuntimeError("Supabase client not initialized")
        
        try:
            logger.info(f"Getting {limit} recent messages for conversation {conversation_id}")
            
            # Optimized query: uses idx_agent_messages_conversation_recent
            msg_response = (
                self.supabase.table("agent_messages")
                .select("id, content, role, agent_type, metadata, created_at")
                .eq("conversation_id", conversation_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            
            # Reverse to get chronological order
            messages = [
                Message(
                    id=msg["id"],
                    content=msg["content"],
                    role=msg["role"],
                    timestamp=datetime.fromisoformat(msg["created_at"].replace("Z", "+00:00")),
                    agent_type=msg.get("agent_type"),
                    metadata=msg.get("metadata", {}),
                )
                for msg in reversed(msg_response.data)
            ]
            
            logger.info(f"Retrieved {len(messages)} recent messages")
            return messages
            
        except Exception as e:
            logger.error(f"Error getting recent messages: {e}", exc_info=True)
            raise
    
    async def delete_conversation(
        self,
        conversation_id: str,
        user_id: str
    ) -> bool:
        """
        Delete a conversation and its messages.
        
        Args:
            conversation_id: Conversation ID
            user_id: User ID (for authorization)
            
        Returns:
            True if deleted successfully
        """
        if not self.supabase:
            raise RuntimeError("Supabase client not initialized")
        
        try:
            logger.info(f"Deleting conversation {conversation_id}")
            
            # Verify ownership
            conv_response = (
                self.supabase.table("agent_conversations")
                .select("id")
                .eq("id", conversation_id)
                .eq("user_id", user_id)
                .single()
                .execute()
            )
            
            if not conv_response.data:
                raise ValueError(f"Conversation {conversation_id} not found or unauthorized")
            
            # Delete conversation (messages will cascade delete)
            self.supabase.table("agent_conversations").delete().eq("id", conversation_id).execute()
            
            logger.info(f"Deleted conversation {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting conversation: {e}", exc_info=True)
            raise
    
    async def save_message(
        self,
        conversation_id: str,
        content: str,
        role: str,
        agent_type: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> Message:
        """
        Save a message to a conversation.
        
        Args:
            conversation_id: Conversation ID
            content: Message content
            role: Message role (user or assistant)
            agent_type: Agent type (for assistant messages)
            metadata: Additional metadata
            
        Returns:
            Saved message
        """
        if not self.supabase:
            raise RuntimeError("Supabase client not initialized")
        
        try:
            logger.info(f"Saving {role} message to conversation {conversation_id}")
            
            data = {
                "conversation_id": conversation_id,
                "content": content,
                "role": role,
                "agent_type": agent_type,
                "metadata": metadata or {},
            }
            
            response = (
                self.supabase.table("agent_messages")
                .insert(data)
                .execute()
            )
            
            message = Message(
                id=response.data[0]["id"],
                content=content,
                role=role,
                timestamp=datetime.fromisoformat(response.data[0]["created_at"].replace("Z", "+00:00")),
                agent_type=agent_type,
                metadata=metadata,
            )
            
            logger.info(f"Saved message {message.id}")
            return message
            
        except Exception as e:
            logger.error(f"Error saving message: {e}", exc_info=True)
            raise
