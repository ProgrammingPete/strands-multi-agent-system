"""
Conversation service for managing conversations and messages in Supabase.
"""
import logging
from typing import List, Optional
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.supabase_client import get_supabase_client
from backend.models import (
    ConversationCreate,
    ConversationResponse,
    ConversationWithMessages,
    Message,
)

logger = logging.getLogger(__name__)


class ConversationService:
    """Service for managing conversations and messages."""
    
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
        limit: int = 50
    ) -> List[ConversationResponse]:
        """
        List conversations for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of conversations to return
            
        Returns:
            List of conversations
        """
        if not self.supabase:
            raise RuntimeError("Supabase client not initialized")
        
        try:
            logger.info(f"Listing conversations for user {user_id}")
            
            if not user_id:
                raise ValueError("User ID is required")
            
            response = (
                self.supabase.table("agent_conversations")
                .select("*")
                .eq("user_id", user_id)
                .order("updated_at", desc=True)
                .limit(limit)
                .execute()
            )
            
            conversations = [
                ConversationResponse(**conv) for conv in response.data
            ]
            
            logger.info(f"Found {len(conversations)} conversations")
            return conversations
            
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
        user_id: str
    ) -> ConversationWithMessages:
        """
        Get a conversation with its messages.
        
        Args:
            conversation_id: Conversation ID
            user_id: User ID (for authorization)
            
        Returns:
            Conversation with messages
        """
        if not self.supabase:
            raise RuntimeError("Supabase client not initialized")
        
        try:
            logger.info(f"Getting conversation {conversation_id}")
            
            # Get conversation
            conv_response = (
                self.supabase.table("agent_conversations")
                .select("*")
                .eq("id", conversation_id)
                .eq("user_id", user_id)
                .single()
                .execute()
            )
            
            if not conv_response.data:
                raise ValueError(f"Conversation {conversation_id} not found")
            
            # Get messages
            msg_response = (
                self.supabase.table("agent_messages")
                .select("*")
                .eq("conversation_id", conversation_id)
                .order("created_at", desc=False)
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
                **conv_response.data,
                messages=messages
            )
            
            logger.info(f"Found conversation with {len(messages)} messages")
            return conversation
            
        except Exception as e:
            logger.error(f"Error getting conversation: {e}", exc_info=True)
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
