# FastAPI Backend Service

This is the FastAPI backend service for the Canvalo multi-agent chat system. It provides REST API endpoints for streaming chat responses and managing conversations.

## Features

- **Server-Sent Events (SSE) Streaming**: Real-time token-by-token streaming of AI responses
- **Conversation Management**: Create, list, retrieve, and delete conversations
- **Error Handling**: Comprehensive error handling with retry logic and user-friendly messages
- **CORS Support**: Configured for frontend integration
- **Logging**: Structured logging for debugging and monitoring

## Architecture

```
backend/
├── __init__.py              # Package initialization
├── main.py                  # FastAPI application and endpoints
├── config.py                # Configuration and settings
├── models.py                # Pydantic models for validation
├── chat_service.py          # Chat streaming service
├── conversation_service.py  # Conversation management service
├── error_handler.py         # Error handling and retry logic
└── README.md               # This file
```

## Installation

1. Install dependencies:
```bash
cd strands-multi-agent-system
uv sync
```

2. Configure environment variables in `.env`:
```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key-here

# AWS Configuration
AWS_REGION=us-east-1
AWS_PROFILE=your-profile

# Bedrock Configuration
BEDROCK_MODEL_ID=amazon.nova-lite-v1:0

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

## Running the Server

### Development Mode
```bash
python -m backend.main
```

Or with uvicorn directly:
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
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
GET /api/conversations?user_id=uuid&limit=50
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
GET /api/conversations/{conversation_id}?user_id=uuid
```

#### Delete Conversation
```
DELETE /api/conversations/{conversation_id}?user_id=uuid
```

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

## Configuration

All configuration is managed through environment variables and the `config.py` module:

- **Supabase**: Database connection
- **AWS Bedrock**: LLM model configuration
- **CORS**: Allowed origins for frontend
- **Retry**: Max attempts, delays
- **API**: Host and port

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

## Testing

Run tests with pytest:
```bash
pytest tests/
```

## Deployment

### Docker (Recommended)
```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY . .
RUN pip install uv && uv sync
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables
Ensure all required environment variables are set in production:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`
- `AWS_REGION`
- `BEDROCK_MODEL_ID`

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

## Support

For issues or questions:
1. Check logs for error details
2. Review configuration settings
3. Test with health check endpoint
4. Contact development team
