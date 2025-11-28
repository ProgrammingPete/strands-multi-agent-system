"""
Context management utilities for building and managing conversation context.
Handles loading conversation history, formatting for LLM, and context summarization.
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from backend.models import Message, ChatRequest
from backend.conversation_service import ConversationService
from backend.config import settings

logger = logging.getLogger(__name__)


class ContextManager:
    """
    Manages conversation context for LLM interactions.
    
    Responsibilities:
    - Load conversation history from database
    - Format messages for LLM context
    - Add user profile information
    - Detect and handle token limit exceeded
    - Summarize older messages when needed
    - Persist messages to database
    """
    
    # Token limits for different models
    TOKEN_LIMITS = {
        "amazon.nova-lite-v1:0": 300000,  # 300K context window
        "amazon.nova-pro-v1:0": 300000,   # 300K context window
        "anthropic.claude-3-haiku-20240307-v1:0": 200000,  # 200K context window
    }
    
    # Approximate tokens per character (rough estimate)
    CHARS_PER_TOKEN = 4
    
    # Number of recent messages to always preserve
    PRESERVE_RECENT_MESSAGES = 10
    
    def __init__(self, conversation_service: Optional[ConversationService] = None):
        """
        Initialize the context manager.
        
        Args:
            conversation_service: Optional conversation service instance
        """
        self.conversation_service = conversation_service or ConversationService()
        self.model_id = settings.bedrock_model_id
        self.token_limit = self.TOKEN_LIMITS.get(self.model_id, 200000)
        logger.info(f"ContextManager initialized with model {self.model_id}, token limit {self.token_limit}")
    
    async def build_context(
        self,
        request: ChatRequest,
        include_user_profile: bool = True
    ) -> str:
        """
        Build context string from conversation history and user profile.
        
        Args:
            request: Chat request with conversation ID and history
            include_user_profile: Whether to include user profile information
            
        Returns:
            Formatted context string for LLM
        """
        try:
            logger.info(f"Building context for conversation {request.conversation_id}")
            
            # Load full conversation history from database if not provided
            history = request.history
            if not history and request.conversation_id:
                history = await self._load_conversation_history(
                    request.conversation_id,
                    request.user_id
                )
            
            # Check if context exceeds token limit
            if self._exceeds_token_limit(history):
                logger.info("Context exceeds token limit, summarizing older messages")
                history = await self._summarize_context(history)
            
            # Format messages for LLM
            context_parts = []
            
            # Add user profile if requested
            if include_user_profile:
                user_profile = await self._get_user_profile(request.user_id)
                if user_profile:
                    context_parts.append(user_profile)
            
            # Add conversation history
            if history:
                context_parts.append("Previous conversation:")
                for msg in history:
                    role = "User" if msg.role == "user" else "Assistant"
                    context_parts.append(f"{role}: {msg.content}")
            
            context = "\n".join(context_parts)
            
            logger.info(f"Built context with {len(history)} messages, {len(context)} characters")
            return context
            
        except Exception as e:
            logger.error(f"Error building context: {e}", exc_info=True)
            # Return empty context on error to allow conversation to continue
            return ""
    
    async def _load_conversation_history(
        self,
        conversation_id: str,
        user_id: str,
        use_recent_only: bool = True
    ) -> List[Message]:
        """
        Load conversation history from database.
        
        Optimized: Uses get_recent_messages for context building
        to avoid loading entire conversation history.
        
        Args:
            conversation_id: Conversation ID
            user_id: User ID for authorization
            use_recent_only: If True, only load recent messages for context
            
        Returns:
            List of messages in chronological order
        """
        try:
            if use_recent_only:
                # Optimized path: only load recent messages for context
                # Uses idx_agent_messages_conversation_recent index
                messages = await self.conversation_service.get_recent_messages(
                    conversation_id,
                    limit=self.PRESERVE_RECENT_MESSAGES * 2  # Load extra for summarization
                )
                logger.info(f"Loaded {len(messages)} recent messages for context")
                return messages
            else:
                # Full history path: load all messages (paginated)
                conversation = await self.conversation_service.get_conversation(
                    conversation_id,
                    user_id
                )
                return conversation.messages
        except Exception as e:
            logger.error(f"Error loading conversation history: {e}", exc_info=True)
            return []
    
    async def _get_user_profile(self, user_id: str) -> Optional[str]:
        """
        Get user profile information to add to context.
        
        Args:
            user_id: User ID
            
        Returns:
            Formatted user profile string or None
        """
        try:
            # TODO: Implement user profile loading from Supabase
            # For now, return a basic profile
            return f"User ID: {user_id}\nBusiness Type: Painting Contractor"
        except Exception as e:
            logger.error(f"Error loading user profile: {e}", exc_info=True)
            return None
    
    def _exceeds_token_limit(self, messages: List[Message]) -> bool:
        """
        Check if message history exceeds token limit.
        
        Args:
            messages: List of messages
            
        Returns:
            True if exceeds limit, False otherwise
        """
        if not messages:
            return False
        
        # Estimate token count from character count
        total_chars = sum(len(msg.content) for msg in messages)
        estimated_tokens = total_chars // self.CHARS_PER_TOKEN
        
        # Add buffer for formatting and system prompts (20%)
        estimated_tokens = int(estimated_tokens * 1.2)
        
        exceeds = estimated_tokens > self.token_limit
        
        if exceeds:
            logger.info(
                f"Context exceeds token limit: {estimated_tokens} > {self.token_limit}"
            )
        
        return exceeds
    
    async def _summarize_context(self, messages: List[Message]) -> List[Message]:
        """
        Summarize older messages to reduce token count while preserving recent messages.
        
        Strategy:
        - Keep the most recent N messages unchanged
        - Summarize older messages into a single summary message
        - Preserve important information (user requests, agent actions)
        
        Args:
            messages: List of messages to summarize
            
        Returns:
            List of messages with older messages summarized
        """
        if len(messages) <= self.PRESERVE_RECENT_MESSAGES:
            return messages
        
        try:
            # Split into old and recent messages
            old_messages = messages[:-self.PRESERVE_RECENT_MESSAGES]
            recent_messages = messages[-self.PRESERVE_RECENT_MESSAGES:]
            
            # Create summary of old messages
            summary_parts = ["Summary of earlier conversation:"]
            
            # Extract key information from old messages
            user_requests = []
            agent_actions = []
            
            for msg in old_messages:
                if msg.role == "user":
                    # Keep track of user requests
                    if len(msg.content) < 200:
                        user_requests.append(msg.content)
                    else:
                        user_requests.append(msg.content[:200] + "...")
                elif msg.role == "assistant":
                    # Extract agent actions from metadata
                    if msg.metadata and "toolCalls" in msg.metadata:
                        for tool_call in msg.metadata["toolCalls"]:
                            agent_actions.append(
                                f"{tool_call.get('name', 'unknown')} action"
                            )
            
            # Build summary
            if user_requests:
                summary_parts.append(f"User asked about: {', '.join(user_requests[:5])}")
            if agent_actions:
                summary_parts.append(f"Actions taken: {', '.join(set(agent_actions[:5]))}")
            
            summary_content = "\n".join(summary_parts)
            
            # Create summary message
            summary_message = Message(
                id="summary",
                content=summary_content,
                role="assistant",
                timestamp=old_messages[-1].timestamp if old_messages else datetime.now(),
                metadata={"is_summary": True}
            )
            
            # Return summary + recent messages
            summarized = [summary_message] + recent_messages
            
            logger.info(
                f"Summarized {len(old_messages)} old messages, "
                f"kept {len(recent_messages)} recent messages"
            )
            
            return summarized
            
        except Exception as e:
            logger.error(f"Error summarizing context: {e}", exc_info=True)
            # On error, just return recent messages
            return messages[-self.PRESERVE_RECENT_MESSAGES:]
    
    async def save_message(
        self,
        conversation_id: str,
        content: str,
        role: str,
        agent_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Message]:
        """
        Save a message to the database and update conversation metadata.
        
        Args:
            conversation_id: Conversation ID
            content: Message content
            role: Message role (user or assistant)
            agent_type: Agent type (for assistant messages)
            metadata: Additional metadata
            
        Returns:
            Saved message or None on error
        """
        try:
            message = await self.conversation_service.save_message(
                conversation_id=conversation_id,
                content=content,
                role=role,
                agent_type=agent_type,
                metadata=metadata
            )
            
            logger.info(f"Saved {role} message to conversation {conversation_id}")
            return message
            
        except Exception as e:
            logger.error(f"Error saving message: {e}", exc_info=True)
            return None
    
    def format_messages_for_llm(self, messages: List[Message]) -> str:
        """
        Format messages into a string suitable for LLM context.
        
        Args:
            messages: List of messages
            
        Returns:
            Formatted string
        """
        if not messages:
            return ""
        
        formatted_parts = []
        for msg in messages:
            role = "User" if msg.role == "user" else "Assistant"
            formatted_parts.append(f"{role}: {msg.content}")
        
        return "\n".join(formatted_parts)
    
    def estimate_token_count(self, text: str) -> int:
        """
        Estimate token count for a text string.
        
        Args:
            text: Text to estimate
            
        Returns:
            Estimated token count
        """
        return len(text) // self.CHARS_PER_TOKEN
