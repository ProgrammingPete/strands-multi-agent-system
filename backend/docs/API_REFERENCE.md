# API Reference

Complete API documentation for the Canvalo Multi-Agent FastAPI Backend.

## Architecture Overview

The backend follows a layered architecture pattern optimized for AI agent interactions:

```
┌─────────────────────────────────────────────────────────────────┐
│                    API LAYER                                     │
│  FastAPI Application (main.py)                                  │
│  - OpenAPI/Swagger documentation                                │
│  - CORS middleware for frontend integration                     │
│  - Request/response logging and validation                      │
│  - Health checks and service status                             │
└─────────────────┬───────────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────────┐
│                 SERVICE LAYER                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  chat_service.py - SSE streaming with agent routing     │   │
│  │  conversation_service.py - Conversation CRUD operations │   │
│  │  context_manager.py - Context building & summarization  │   │
│  │  auth_middleware.py - JWT validation & user isolation   │   │
│  │  error_handler.py - Retry logic & error translation     │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────┬───────────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────────┐
│                 AGENT LAYER                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  supervisor.py - Intelligent query routing              │   │
│  │  9 specialized agents with Supabase CRUD tools         │   │
│  │  Natural language processing for business operations    │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────┬───────────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────────┐
│                 DATA LAYER                                       │
│  Supabase PostgreSQL with Row-Level Security (RLS)             │
│  - 9 business entity tables with user isolation                │
│  - Conversations and messages with pagination                  │
│  - Real-time subscriptions and authentication                  │
└─────────────────────────────────────────────────────────────────┘
```

### File Structure
```
backend/
├── __init__.py              # Package initialization
├── main.py                  # FastAPI application and endpoints
├── config.py                # Configuration management with Pydantic Settings
├── models.py                # Pydantic models for request/response validation
├── auth_middleware.py       # JWT validation and user authentication
├── admin_auth.py            # Admin authentication for privileged operations
├── chat_service.py          # Chat streaming service with SSE
├── conversation_service.py  # Conversation management with Supabase
├── context_manager.py       # Context building and token management
├── error_handler.py         # Error handling with retry logic and user-friendly messages
└── docs/                    # Comprehensive documentation
```

## API Endpoints

### Health & Status Endpoints

#### Root Endpoint
```http
GET /
```

**Response:**
```json
{
  "message": "Canvalo Multi-Agent Backend API",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/health"
}
```

#### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00Z",
  "supabase_configured": true,
  "bedrock_model": "amazon.nova-lite-v1:0",
  "environment": "development",
  "agents_available": 9,
  "configuration": {
    "jwt_required": false,
    "cors_enabled": true,
    "admin_auth_configured": true
  }
}
```

**Status Codes:**
- `200`: Service healthy and all dependencies available
- `503`: Service unhealthy or dependencies unavailable

### Multi-Agent Chat Streaming

#### Stream Chat Response
```http
POST /api/chat/stream
Content-Type: application/json
Authorization: Bearer <jwt_token>  # Required in production

{
  "message": "What invoices do I have?",
  "conversation_id": "uuid",
  "user_id": "uuid", 
  "history": [
    {
      "role": "user",
      "content": "Previous message",
      "timestamp": "2025-01-15T10:25:00Z"
    },
    {
      "role": "assistant", 
      "content": "Previous response",
      "timestamp": "2025-01-15T10:25:30Z"
    }
  ]
}
```

**Request Fields:**
- `message` (required): User's natural language query
- `conversation_id` (required): UUID for conversation tracking
- `user_id` (required): User ID for authorization and data scoping
- `history` (optional): Previous conversation messages for context

**Response Format (Server-Sent Events):**
```
data: {"type":"token","content":"I can help you","agent_type":"supervisor"}

data: {"type":"token","content":" with invoices.","agent_type":"supervisor"}

data: {"type":"agent_routing","agent":"invoices","query":"user invoice request"}

data: {"type":"token","content":"You have 3 invoices:","agent_type":"invoices"}

data: {"type":"tool_call","tool":"get_invoices","status":"executing"}

data: {"type":"token","content":" Invoice #001 ($1,200)","agent_type":"invoices"}

data: {"type":"complete","agent_type":"invoices","tokens_used":45}
```

**SSE Chunk Types:**
- `token`: Text token from LLM response
- `agent_routing`: Agent selection and query routing information
- `tool_call`: Agent tool execution status
- `complete`: Stream finished successfully
- `error`: Error occurred during processing

**Status Codes:**
- `200`: Stream started successfully
- `400`: Invalid request format or missing required fields
- `401`: Authentication required (production mode)
- `403`: User not authorized for conversation
- `500`: Internal server error

**Example Agent Interactions:**
```bash
# Invoice query
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Show me overdue invoices",
    "conversation_id": "conv-123",
    "user_id": "user-456"
  }'

# Appointment scheduling  
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Schedule a meeting with John Smith next Tuesday",
    "conversation_id": "conv-124", 
    "user_id": "user-456"
  }'

# Multi-agent coordination
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is my revenue this month and which clients need follow-up?",
    "conversation_id": "conv-125",
    "user_id": "user-456"
  }'
```

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
SUPABASE_PUB_KEY=your-pub-key-here          # Required for user operations
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
settings.SUPABASE_PUB_KEY  # Anon key for user-scoped operations
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
