"""
Chat service for handling streaming responses from the supervisor agent.
"""
import logging
import json
import asyncio
import os
from typing import AsyncGenerator

from agents.supervisor import create_supervisor_agent
from backend.models import ChatRequest, StreamChunk, AgentType
from backend.error_handler import retry_with_backoff, translate_error_to_user_message
from backend.context_manager import ContextManager

logger = logging.getLogger(__name__)


class ChatService:
    """Service for handling chat requests and streaming responses."""
    
    def __init__(self):
        """Initialize the chat service."""
        self.context_manager = ContextManager()
        logger.info("ChatService initialized with context manager")
    
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
            logger.info(f"User ID: {request.user_id}")
            
            # Save user message to database
            await self.context_manager.save_message(
                conversation_id=request.conversation_id,
                content=request.message,
                role="user"
            )
            
            # Build context from history using context manager
            context = await self.context_manager.build_context(request)
            
            # Add user_id to context for tools to use
            context_with_user = f"[SYSTEM: User ID is {request.user_id}]\n\n{context}"
            
            # Collect full response for saving
            full_response = []
            
            # Stream response from supervisor agent
            async for chunk in self._stream_from_agent(request.message, context_with_user, request.user_id):
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
        context: str,
        user_id: str
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Stream response from supervisor agent with retry logic.
        
        Args:
            message: User message
            context: Conversation context (includes user_id)
            user_id: User ID for tool calls
            
        Yields:
            StreamChunk objects with tokens and tool calls
        """
        import queue
        
        # Combine context and message
        full_prompt = f"{context}\n\nUser: {message}" if context else message
        
        # Store user_id in environment for tools to access
        os.environ['CURRENT_USER_ID'] = user_id
        
        # Thread-safe queue for streaming events
        event_queue: queue.Queue = queue.Queue()
        streaming_complete = asyncio.Event()
        agent_error = None
        
        def streaming_callback(**kwargs):
            """Callback handler to capture streaming tokens."""
            data = kwargs.get("data", "")
            complete = kwargs.get("complete", False)
            current_tool_use = kwargs.get("current_tool_use", {})
            
            # Stream text tokens
            if data:
                event_queue.put(('token', data))
            
            # Track tool usage
            if current_tool_use and current_tool_use.get("name"):
                tool_name = current_tool_use.get("name", "Unknown")
                event_queue.put(('tool_start', {'name': tool_name}))
        
        def run_agent():
            """Run agent in thread with streaming callback."""
            nonlocal agent_error
            try:
                # Create agent with streaming callback
                streaming_agent = create_supervisor_agent(callback_handler=streaming_callback)
                streaming_agent(full_prompt)
                event_queue.put(('done', None))
            except Exception as e:
                agent_error = e
                event_queue.put(('error', str(e)))
            finally:
                streaming_complete.set()
        
        try:
            # Start agent in background thread
            loop = asyncio.get_running_loop()
            agent_task = loop.run_in_executor(None, run_agent)
            
            # Track seen tools to avoid duplicate events
            seen_tools = set()
            
            # Yield events as they arrive
            while not streaming_complete.is_set() or not event_queue.empty():
                try:
                    # Non-blocking check with small timeout
                    event_type, event_data = event_queue.get(timeout=0.05)
                    
                    if event_type == 'token':
                        yield StreamChunk(
                            type="token",
                            content=event_data,
                            agent_type=AgentType.SUPERVISOR
                        )
                    elif event_type == 'tool_start':
                        tool_name = event_data.get('name')
                        # Only emit tool_start once per tool invocation
                        if tool_name and tool_name not in seen_tools:
                            seen_tools.add(tool_name)
                            yield StreamChunk(
                                type="tool_start",
                                tool_name=tool_name,
                                agent_type=AgentType.SUPERVISOR
                            )
                    elif event_type == 'error':
                        raise Exception(event_data)
                    elif event_type == 'done':
                        break
                        
                except queue.Empty:
                    # Allow other async tasks to run
                    await asyncio.sleep(0.01)
                    continue
            
            # Ensure agent task completes
            await agent_task
            
            if agent_error:
                raise agent_error
        
        except asyncio.CancelledError:
            logger.info("Client disconnected, stopping stream")
            raise
        except Exception as e:
            logger.error(f"Error streaming from agent after retries: {e}", exc_info=True)
            raise
