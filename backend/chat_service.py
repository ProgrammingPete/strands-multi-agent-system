"""
Chat service for handling streaming responses from the supervisor agent.

Performance optimizations (Task 23.2):
- Reduced queue polling timeout for lower latency
- Token batching to reduce SSE overhead
- Configurable streaming parameters
- Optimized async sleep intervals
"""
import logging
import json
import asyncio
import os
import time
from typing import AsyncGenerator, List

from agents.supervisor import create_supervisor_agent
from backend.models import ChatRequest, StreamChunk, AgentType
from backend.error_handler import retry_with_backoff, translate_error_to_user_message
from backend.context_manager import ContextManager

logger = logging.getLogger(__name__)

# Streaming optimization constants
# Queue polling timeout in seconds (lower = more responsive, higher CPU)
QUEUE_POLL_TIMEOUT = 0.02  # 20ms - optimized from 50ms

# Async sleep interval when queue is empty (lower = more responsive)
ASYNC_SLEEP_INTERVAL = 0.005  # 5ms - optimized from 10ms

# Token batching settings
# Batch tokens together if they arrive within this window (reduces SSE overhead)
TOKEN_BATCH_WINDOW_MS = 10  # 10ms window for batching
TOKEN_BATCH_MAX_SIZE = 5  # Maximum tokens to batch together

# Minimum time between SSE events (prevents overwhelming the client)
MIN_SSE_INTERVAL_MS = 5  # 5ms minimum between events


class ChatService:
    """Service for handling chat requests and streaming responses with optimized latency."""
    
    def __init__(self):
        """Initialize the chat service."""
        self.context_manager = ContextManager()
        self._last_sse_time = 0
        self._created_conversations = set()  # Track conversations we've created this session
        logger.info("ChatService initialized with optimized streaming")
    
    async def _ensure_conversation_exists(
        self,
        conversation_id: str,
        user_id: str,
        jwt_token: str = None
    ) -> None:
        """
        Ensure a conversation exists before saving messages.
        Creates the conversation if it doesn't exist.
        
        Args:
            conversation_id: Conversation ID
            user_id: User ID
            jwt_token: Optional JWT token for user-scoped operations
        """
        # Skip if we already created this conversation in this session
        if conversation_id in self._created_conversations:
            return
        
        try:
            from backend.conversation_service import ConversationService
            from backend.models import ConversationCreate
            
            service = ConversationService()
            
            # Try to get the conversation first
            try:
                await service.get_conversation(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    message_limit=1,
                    jwt_token=jwt_token
                )
                # Conversation exists, mark it and return
                self._created_conversations.add(conversation_id)
                logger.info(f"Conversation {conversation_id} already exists")
                return
            except ValueError:
                # Conversation doesn't exist, create it
                pass
            
            # Create the conversation
            logger.info(f"Creating conversation {conversation_id} for user {user_id}")
            
            # Use the Supabase client directly to insert with specific ID
            import os
            environment = os.getenv("ENVIRONMENT", "development")
            
            if environment == "development":
                client = service.supabase.client
            elif jwt_token:
                client = service.supabase.create_user_scoped_client(jwt_token)
            else:
                client = service.supabase.client
            
            data = {
                "id": conversation_id,
                "user_id": user_id,
                "title": "AI Chat",
                "metadata": {},
            }
            
            client.schema("api").table("agent_conversations").insert(data).execute()
            
            self._created_conversations.add(conversation_id)
            logger.info(f"Created conversation {conversation_id}")
            
        except Exception as e:
            # Log but don't fail - the message save will fail with a clearer error if needed
            logger.warning(f"Could not ensure conversation exists: {e}")
    
    async def stream_chat_response(
        self,
        request: ChatRequest,
        jwt_token: str = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat response from supervisor agent using Server-Sent Events format.
        
        Args:
            request: Chat request with message and context
            jwt_token: Optional JWT token for user-scoped operations (passed to agents)
            
        Yields:
            SSE-formatted strings with streaming chunks
        """
        try:
            logger.info(f"Processing chat request for conversation {request.conversation_id}")
            logger.info(f"User message: {request.message[:100]}...")
            logger.info(f"User ID: {request.user_id}")
            
            # Ensure conversation exists before saving messages (auto-create if needed)
            await self._ensure_conversation_exists(
                conversation_id=request.conversation_id,
                user_id=request.user_id,
                jwt_token=jwt_token
            )
            
            # Save user message to database
            await self.context_manager.save_message(
                conversation_id=request.conversation_id,
                content=request.message,
                role="user",
                user_id=request.user_id,
                jwt_token=jwt_token
            )
            
            # Build context from history using context manager
            context = await self.context_manager.build_context(request)
            
            # Add user_id to context for tools to use
            context_with_user = f"[SYSTEM: User ID is {request.user_id}]\n\n{context}"
            
            # Collect full response for saving
            full_response = []
            
            # Stream response from supervisor agent
            async for chunk in self._stream_from_agent(request.message, context_with_user, request.user_id, jwt_token):
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
                    user_id=request.user_id,
                    agent_type=AgentType.SUPERVISOR.value,
                    jwt_token=jwt_token
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
        user_id: str,
        jwt_token: str = None
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Stream response from supervisor agent with optimized latency.
        
        Performance optimizations:
        - Reduced queue polling timeout (20ms vs 50ms)
        - Token batching to reduce SSE overhead
        - Optimized async sleep intervals (5ms vs 10ms)
        
        Security (Task 5.3):
        - JWT token propagated to agent invocations
        - User-scoped clients used when JWT is provided
        
        Args:
            message: User message
            context: Conversation context (includes user_id)
            user_id: User ID for tool calls
            jwt_token: Optional JWT token for user-scoped database operations
            
        Yields:
            StreamChunk objects with tokens and tool calls
        """
        import queue
        
        # Combine context and message
        full_prompt = f"{context}\n\nUser: {message}" if context else message
        
        # Store user_id in environment for tools to access
        os.environ['CURRENT_USER_ID'] = user_id
        
        # Store JWT token in environment for tools to create user-scoped clients
        if jwt_token:
            os.environ['CURRENT_USER_JWT'] = jwt_token
        elif 'CURRENT_USER_JWT' in os.environ:
            # Clear any previous JWT if not provided
            del os.environ['CURRENT_USER_JWT']
        
        # Thread-safe queue for streaming events
        event_queue: queue.Queue = queue.Queue()
        streaming_complete = asyncio.Event()
        agent_error = None
        
        def streaming_callback(**kwargs):
            """Callback handler to capture streaming tokens."""
            data = kwargs.get("data", "")
            complete = kwargs.get("complete", False)
            current_tool_use = kwargs.get("current_tool_use", {})
            
            # Stream text tokens with timestamp for batching
            if data:
                event_queue.put(('token', data, time.time()))
            
            # Track tool usage
            if current_tool_use and current_tool_use.get("name"):
                tool_name = current_tool_use.get("name", "Unknown")
                event_queue.put(('tool_start', {'name': tool_name}, time.time()))
        
        def run_agent():
            """Run agent in thread with streaming callback."""
            nonlocal agent_error
            try:
                # Create agent with streaming callback
                streaming_agent = create_supervisor_agent(callback_handler=streaming_callback)
                streaming_agent(full_prompt)
                event_queue.put(('done', None, time.time()))
            except Exception as e:
                agent_error = e
                event_queue.put(('error', str(e), time.time()))
            finally:
                streaming_complete.set()
        
        try:
            # Start agent in background thread
            loop = asyncio.get_running_loop()
            agent_task = loop.run_in_executor(None, run_agent)
            
            # Track seen tools to avoid duplicate events
            seen_tools = set()
            
            # Token batching buffer
            token_buffer: List[str] = []
            last_token_time = 0
            
            # Yield events as they arrive with optimized polling
            while not streaming_complete.is_set() or not event_queue.empty():
                try:
                    # Optimized: reduced timeout from 50ms to 20ms
                    event_type, event_data, event_time = event_queue.get(timeout=QUEUE_POLL_TIMEOUT)
                    
                    if event_type == 'token':
                        # Token batching: collect tokens that arrive close together
                        token_buffer.append(event_data)
                        last_token_time = event_time
                        
                        # Flush buffer if max size reached or enough time passed
                        should_flush = (
                            len(token_buffer) >= TOKEN_BATCH_MAX_SIZE or
                            (time.time() - last_token_time) * 1000 > TOKEN_BATCH_WINDOW_MS
                        )
                        
                        if should_flush and token_buffer:
                            # Batch tokens together for single SSE event
                            batched_content = "".join(token_buffer)
                            token_buffer.clear()
                            yield StreamChunk(
                                type="token",
                                content=batched_content,
                                agent_type=AgentType.SUPERVISOR
                            )
                            
                    elif event_type == 'tool_start':
                        # Flush any pending tokens before tool event
                        if token_buffer:
                            batched_content = "".join(token_buffer)
                            token_buffer.clear()
                            yield StreamChunk(
                                type="token",
                                content=batched_content,
                                agent_type=AgentType.SUPERVISOR
                            )
                        
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
                        # Flush any pending tokens before error
                        if token_buffer:
                            batched_content = "".join(token_buffer)
                            token_buffer.clear()
                            yield StreamChunk(
                                type="token",
                                content=batched_content,
                                agent_type=AgentType.SUPERVISOR
                            )
                        raise Exception(event_data)
                    elif event_type == 'done':
                        # Flush any remaining tokens
                        if token_buffer:
                            batched_content = "".join(token_buffer)
                            token_buffer.clear()
                            yield StreamChunk(
                                type="token",
                                content=batched_content,
                                agent_type=AgentType.SUPERVISOR
                            )
                        break
                        
                except queue.Empty:
                    # Flush buffer on timeout if we have pending tokens
                    if token_buffer and (time.time() - last_token_time) * 1000 > TOKEN_BATCH_WINDOW_MS:
                        batched_content = "".join(token_buffer)
                        token_buffer.clear()
                        yield StreamChunk(
                            type="token",
                            content=batched_content,
                            agent_type=AgentType.SUPERVISOR
                        )
                    
                    # Optimized: reduced sleep from 10ms to 5ms
                    await asyncio.sleep(ASYNC_SLEEP_INTERVAL)
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
