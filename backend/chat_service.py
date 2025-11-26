"""
Chat service for handling streaming responses from the supervisor agent.
"""
import logging
import json
import asyncio
from typing import AsyncGenerator
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.supervisor import supervisor_agent
from backend.models import ChatRequest, StreamChunk, AgentType
from backend.error_handler import retry_with_backoff, translate_error_to_user_message
from backend.context_manager import ContextManager

logger = logging.getLogger(__name__)


class ChatService:
    """Service for handling chat requests and streaming responses."""
    
    def __init__(self):
        """Initialize the chat service."""
        self.supervisor = supervisor_agent
        self.context_manager = ContextManager()
        logger.info("ChatService initialized with supervisor agent and context manager")
    
    async def stream_chat_response(
        self,
        request: ChatRequest
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat response from supervisor agent using Server-Sent Events format.
        
        Args:
            request: Chat request with message and context
            
        Yields:
            SSE-formatted strings with streaming chunks
        """
        try:
            logger.info(f"Processing chat request for conversation {request.conversation_id}")
            logger.info(f"User message: {request.message[:100]}...")
            
            # Save user message to database
            await self.context_manager.save_message(
                conversation_id=request.conversation_id,
                content=request.message,
                role="user"
            )
            
            # Build context from history using context manager
            context = await self.context_manager.build_context(request)
            
            # Collect full response for saving
            full_response = []
            
            # Stream response from supervisor agent
            async for chunk in self._stream_from_agent(request.message, context):
                # Collect tokens for full response
                if chunk.type == "token" and chunk.content:
                    full_response.append(chunk.content)
                
                # Format as SSE
                sse_data = f"data: {json.dumps(chunk.model_dump())}\n\n"
                yield sse_data
            
            # Save assistant message to database
            if full_response:
                await self.context_manager.save_message(
                    conversation_id=request.conversation_id,
                    content="".join(full_response),
                    role="assistant",
                    agent_type=AgentType.SUPERVISOR.value
                )
            
            # Send completion chunk
            completion_chunk = StreamChunk(
                type="complete",
                agent_type=AgentType.SUPERVISOR
            )
            yield f"data: {json.dumps(completion_chunk.model_dump())}\n\n"
            
            logger.info(f"Completed streaming response for conversation {request.conversation_id}")
            
        except Exception as e:
            logger.error(f"Error in stream_chat_response: {e}", exc_info=True)
            
            # Send error chunk
            error_message = translate_error_to_user_message(e)
            error_chunk = StreamChunk(
                type="error",
                error=error_message
            )
            yield f"data: {json.dumps(error_chunk.model_dump())}\n\n"

    
    async def _stream_from_agent(
        self,
        message: str,
        context: str
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Stream response from supervisor agent with retry logic.
        
        Args:
            message: User message
            context: Conversation context
            
        Yields:
            StreamChunk objects with tokens and tool calls
        """
        # Combine context and message
        full_prompt = f"{context}\n\nUser: {message}" if context else message
        
        try:
            # Use retry wrapper for LLM calls
            async def invoke_agent():
                try:
                    return await asyncio.to_thread(self.supervisor, full_prompt)
                except Exception as e:
                    # Log the error and re-raise for retry logic
                    logger.warning(f"Agent invocation failed: {e}")
                    raise
            
            response = await retry_with_backoff(invoke_agent)
            
            # For now, yield the complete response as tokens
            # In a real implementation, we would stream tokens from the LLM
            response_text = str(response)
            
            # Simulate token streaming by chunking the response
            chunk_size = 20  # Characters per chunk
            for i in range(0, len(response_text), chunk_size):
                chunk_text = response_text[i:i + chunk_size]
                yield StreamChunk(
                    type="token",
                    content=chunk_text,
                    agent_type=AgentType.SUPERVISOR
                )
                # Small delay to simulate streaming
                await asyncio.sleep(0.01)
        
        except asyncio.CancelledError:
            # Handle client disconnection gracefully
            logger.info("Client disconnected, stopping stream")
            raise
        except Exception as e:
            logger.error(f"Error streaming from agent after retries: {e}", exc_info=True)
            raise
