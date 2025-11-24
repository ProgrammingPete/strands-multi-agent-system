# Context Management Implementation

## Overview

This document describes the context management implementation for the multi-agent chat system. Context management handles conversation history, token limits, summarization, and message persistence.

## Components

### 1. ContextManager (`backend/context_manager.py`)

The `ContextManager` class is responsible for:

- **Loading conversation history** from the database
- **Formatting messages** for LLM context
- **Adding user profile information** to context
- **Detecting token limit exceeded** situations
- **Summarizing older messages** when context is too large
- **Persisting messages** to the database

#### Key Features

**Token Limit Management:**
- Supports multiple Bedrock models with different token limits:
  - Amazon Nova Lite: 300K tokens
  - Amazon Nova Pro: 300K tokens
  - Claude 3 Haiku: 200K tokens
- Estimates token count from character count (4 chars per token)
- Adds 20% buffer for formatting and system prompts

**Context Summarization:**
- Preserves the most recent 10 messages unchanged
- Summarizes older messages into a single summary message
- Extracts key information:
  - User requests (up to 200 chars each)
  - Agent actions from metadata
- Creates a summary message with `is_summary` flag in metadata

**Message Persistence:**
- Saves messages to `agent_messages` table
- Updates conversation metadata automatically (via database trigger)
- Handles errors gracefully to allow conversation to continue

### 2. ChatService Integration (`backend/chat_service.py`)

The `ChatService` now uses `ContextManager` for:

1. **Saving user messages** before processing
2. **Building context** from conversation history
3. **Saving assistant responses** after streaming completes

#### Message Flow

```
User sends message
    ↓
Save user message to database
    ↓
Build context from history (with summarization if needed)
    ↓
Stream response from supervisor agent
    ↓
Collect full response
    ↓
Save assistant message to database
    ↓
Send completion event
```

## Configuration

### Token Limits

Token limits are configured in `ContextManager.TOKEN_LIMITS`:

```python
TOKEN_LIMITS = {
    "amazon.nova-lite-v1:0": 300000,
    "amazon.nova-pro-v1:0": 300000,
    "anthropic.claude-3-haiku-20240307-v1:0": 200000,
}
```

### Preservation Settings

```python
PRESERVE_RECENT_MESSAGES = 10  # Number of recent messages to keep unchanged
CHARS_PER_TOKEN = 4            # Approximate characters per token
```

## API

### ContextManager Methods

#### `build_context(request, include_user_profile=True)`

Builds context string from conversation history and user profile.

**Parameters:**
- `request`: ChatRequest with conversation ID and history
- `include_user_profile`: Whether to include user profile information

**Returns:** Formatted context string for LLM

**Example:**
```python
context = await context_manager.build_context(request)
```

#### `save_message(conversation_id, content, role, agent_type=None, metadata=None)`

Saves a message to the database and updates conversation metadata.

**Parameters:**
- `conversation_id`: Conversation ID
- `content`: Message content
- `role`: Message role ("user" or "assistant")
- `agent_type`: Agent type (for assistant messages)
- `metadata`: Additional metadata

**Returns:** Saved Message object or None on error

**Example:**
```python
message = await context_manager.save_message(
    conversation_id="conv_123",
    content="Hello",
    role="user"
)
```

#### `format_messages_for_llm(messages)`

Formats messages into a string suitable for LLM context.

**Parameters:**
- `messages`: List of Message objects

**Returns:** Formatted string

**Example:**
```python
formatted = context_manager.format_messages_for_llm(messages)
# Output: "User: Hello\nAssistant: Hi there"
```

#### `estimate_token_count(text)`

Estimates token count for a text string.

**Parameters:**
- `text`: Text to estimate

**Returns:** Estimated token count

**Example:**
```python
tokens = context_manager.estimate_token_count("Hello world")
# Returns: 2 (8 chars / 4 chars per token)
```

## Database Schema

### agent_messages Table

Messages are stored in the `agent_messages` table:

```sql
CREATE TABLE api.agent_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES agent_conversations(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    agent_type TEXT CHECK (agent_type IN ('supervisor', 'invoices', ...)),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Automatic Metadata Updates

A database trigger automatically updates conversation metadata when messages are added:

```sql
CREATE TRIGGER update_conversation_on_message_trigger
    AFTER INSERT ON api.agent_messages
    FOR EACH ROW
    EXECUTE FUNCTION update_conversation_on_message();
```

This updates:
- `updated_at`: Current timestamp
- `last_message_at`: Message creation time
- `message_count`: Incremented by 1

## Testing

### Unit Tests

Run verification tests:

```bash
uv run python backend/verify_context_manager.py
```

Tests cover:
- Token limit detection (small and large messages)
- Context summarization (preserving recent messages)
- Message formatting for LLM
- Token estimation

### Integration Tests

Run integration tests:

```bash
uv run python backend/verify_integration.py
```

Tests cover:
- ChatService integration with ContextManager
- Context building with message history
- User profile inclusion
- End-to-end message flow

## Performance Considerations

### Token Estimation

Token estimation uses a simple heuristic (4 chars per token) which is:
- Fast (O(1) calculation)
- Reasonably accurate for English text
- Conservative (tends to overestimate)

For more accurate token counting, consider using a tokenizer library like `tiktoken`.

### Summarization Strategy

The current summarization strategy:
- Preserves recent messages for context continuity
- Extracts key information from older messages
- Creates a single summary message (reduces token count significantly)

**Trade-offs:**
- ✅ Fast and simple
- ✅ Preserves recent context
- ⚠️ May lose some detail from older messages
- ⚠️ Summary is static (not regenerated)

### Database Performance

Message persistence is asynchronous and non-blocking:
- User messages are saved before processing (minimal delay)
- Assistant messages are saved after streaming (no user-facing delay)
- Errors in persistence don't block conversation flow

## Future Enhancements

### 1. Semantic Summarization

Use an LLM to create more intelligent summaries:
- Identify key topics and decisions
- Preserve important context across long conversations
- Generate summaries that maintain conversation coherence

### 2. Selective Context Loading

Load only relevant messages based on:
- Semantic similarity to current query
- Recency and importance
- Agent type (load messages from relevant agents)

### 3. Token Counting Accuracy

Use a proper tokenizer for accurate token counting:
- `tiktoken` for OpenAI models
- Bedrock-specific tokenizers when available
- Cache token counts to avoid recomputation

### 4. Context Caching

Cache built context strings to avoid rebuilding:
- Use Redis or in-memory cache
- Invalidate on new messages
- Set appropriate TTL (5-15 minutes)

### 5. User Profile Enhancement

Load rich user profile data:
- Business information from database
- User preferences and settings
- Recent activity summary
- Business goals and metrics

## Requirements Validation

This implementation satisfies the following requirements:

### Requirement 15.1: Context Initialization
✅ System initializes empty context with user profile information

### Requirement 15.2: Message Appending
✅ Messages are appended to conversation context and persisted to database

### Requirement 15.3: Context Summarization
✅ Context is summarized when it exceeds token limits, preserving recent messages

### Requirement 15.4: Historical Context Access
✅ Agents can access conversation history to resolve references

## Correctness Properties

### Property 5: Context Growth with Messages
✅ For any message exchange, the conversation context grows by exactly 2 messages (user + assistant)

### Property 6: Context Summarization at Token Limit
✅ For any conversation exceeding token limit, the system summarizes older messages while preserving recent messages, and total token count is below the limit

## Conclusion

The context management implementation provides a robust foundation for maintaining conversation history in the multi-agent chat system. It handles token limits intelligently, persists messages reliably, and integrates seamlessly with the chat service.
