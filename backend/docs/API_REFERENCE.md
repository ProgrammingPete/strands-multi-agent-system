# API Reference

Complete API documentation for the Canvalo FastAPI Backend.

## Architecture

```
backend/
├── __init__.py              # Package initialization
├── main.py                  # FastAPI application and endpoints
├── config.py                # Configuration and settings
├── models.py                # Pydantic models for validation
├── auth_middleware.py       # JWT validation and authentication
├── chat_service.py          # Chat streaming service
├── conversation_service.py  # Conversation management service
├── context_manager.py       # Context management
├── error_handler.py         # Error handling and retry logic
└── docs/                    # Documentation
```

## API Endpoints

### Health Check

```
GET /
GET /health
```

Returns service status and configuration.

### Chat Streaming

```
POST /api/chat/stream
Content-Type: application/json

{
  "message": "What invoices do I have?",
  "conversation_id": "uuid",
  "user_id": "uuid",
  "history": []
}
```

Returns Server-Sent Events stream with chat response.

### Conversation Management

#### List Conversations
```
GET /api/conversations?user_id=uuid&limit=50&offset=0
```

**Query Parameters:**
- `user_id` (required): User ID
- `limit` (optional): Maximum conversations to return (default: 50)
- `offset` (optional): Number of conversations to skip for pagination (default: 0)

**Response:**
```json
{
  "conversations": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "title": "Conversation title",
      "created_at": "2025-01-15T10:30:00Z",
      "updated_at": "2025-01-15T10:35:00Z",
      "last_message_at": "2025-01-15T10:35:00Z",
      "message_count": 5,
      "metadata": {}
    }
  ],
  "total": 100,
  "limit": 50,
  "offset": 0,
  "has_more": true
}
```

#### Create Conversation
```
POST /api/conversations
Content-Type: application/json

{
  "user_id": "uuid",
  "title": "Optional title"
}
```

#### Get Conversation with Messages
```
GET /api/conversations/{conversation_id}?user_id=uuid&message_limit=100&message_offset=0
```

**Query Parameters:**
- `user_id` (required): User ID for authorization
- `message_limit` (optional): Maximum messages to return (default: 100, max: 500)
- `message_offset` (optional): Number of messages to skip for pagination (default: 0)

**Response Codes:**
- `200`: Conversation with messages returned
- `404`: Conversation not found or unauthorized
- `500`: Internal server error

#### Delete Conversation
```
DELETE /api/conversations/{conversation_id}?user_id=uuid
```

**Response Codes:**
- `200`: Conversation deleted successfully
- `404`: Conversation not found or unauthorized
- `500`: Internal server error

## Streaming Format

The chat endpoint uses Server-Sent Events (SSE) format:

```
data: {"type": "token", "content": "Hello", "agent_type": "supervisor"}

data: {"type": "token", "content": " world", "agent_type": "supervisor"}

data: {"type": "complete", "agent_type": "supervisor"}
```

Chunk types:
- `token`: Text token from LLM
- `tool_call`: Agent tool execution
- `complete`: Stream finished successfully
- `error`: Error occurred

## Error Handling

The service implements comprehensive error handling:

1. **Retry Logic**: Exponential backoff for LLM failures (3 attempts)
2. **User-Friendly Messages**: Technical errors translated to plain language
3. **Graceful Degradation**: Handles network errors and timeouts
4. **Structured Errors**: Consistent error response format

Example error response:
```json
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "Technical error details",
    "userMessage": "User-friendly explanation",
    "suggestedActions": ["Try again", "Contact support"],
    "retryable": true
  }
}
```

## Configuration

All configuration is managed through environment variables and the `config.py` module:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here          # Required for user operations
SUPABASE_SERVICE_KEY=your-service-key-here    # Optional, dev only

# AWS Configuration
AWS_REGION=us-east-1
AWS_PROFILE=your-profile

# Bedrock Configuration
BEDROCK_MODEL_ID=amazon.nova-lite-v1:0

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Environment Configuration
ENVIRONMENT=development                        # or "production"
SYSTEM_USER_ID=00000000-0000-0000-0000-000000000000  # For testing
```

### Configuration Properties

The `settings` object provides helper properties:

```python
from backend.config import settings

settings.is_production  # True if ENVIRONMENT=production
settings.is_development # True if ENVIRONMENT=development
settings.supabase_anon_key  # Anon key for user-scoped operations
settings.system_user_id     # System user ID for testing
```

## Logging

The service uses Python's built-in logging with structured format:

```
2024-01-15 10:30:45 - backend.main - INFO - Starting FastAPI backend service
2024-01-15 10:30:46 - backend.chat_service - INFO - Processing chat request
```

Log levels:
- `INFO`: Normal operations
- `WARNING`: Retry attempts, non-critical issues
- `ERROR`: Failures, exceptions

## Deployment

### Docker (Recommended)
```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY . .
RUN pip install uv && uv sync
CMD ["uv", "run", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Mode
```bash
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Monitoring

Monitor these metrics in production:
- Request rate and latency
- Error rates by endpoint
- LLM token usage
- Database query performance
- Stream connection duration

## Security

- **Authentication**: Validate user_id from JWT tokens
- **Authorization**: RLS policies in Supabase
- **Rate Limiting**: Implement per-user limits
- **Input Validation**: Pydantic models validate all inputs
- **CORS**: Restricted to allowed origins

## Troubleshooting

### Connection Errors
- Check Supabase URL and service key
- Verify network connectivity
- Check firewall rules

### LLM Errors
- Verify AWS credentials
- Check Bedrock model availability
- Review IAM permissions

### Streaming Issues
- Disable nginx buffering (`X-Accel-Buffering: no`)
- Check client SSE implementation
- Monitor connection timeouts
