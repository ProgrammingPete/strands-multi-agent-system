# FastAPI Backend Service

Backend service for the Canvalo multi-agent chat system.

## Quick Start

```bash
# Start the server
./start_backend.sh

# Or manually
uv run python -m backend.main
```

## Documentation

All documentation has been moved to the `docs/` folder:

- **[Quick Start Guide](docs/QUICK_START.md)** - Get started quickly
- **[Full Documentation](docs/README.md)** - Complete API documentation
- **[Implementation Summary](docs/IMPLEMENTATION_SUMMARY.md)** - Task 15 implementation details
- **[UV Migration Guide](docs/UV_MIGRATION.md)** - Package manager migration notes

## Project Structure

```
backend/
├── __init__.py              # Package initialization
├── main.py                  # FastAPI application
├── config.py                # Configuration management
├── models.py                # Pydantic models
├── chat_service.py          # Chat streaming service
├── conversation_service.py  # Conversation management
├── context_manager.py       # Context management
├── error_handler.py         # Error handling utilities
└── docs/                    # Documentation folder
    ├── README.md            # Full documentation
    ├── QUICK_START.md       # Quick start guide
    ├── IMPLEMENTATION_SUMMARY.md
    └── UV_MIGRATION.md
```

## API Endpoints

- `GET /health` - Health check
- `POST /api/chat/stream` - Stream chat responses (SSE)
- `GET /api/conversations` - List conversations
- `POST /api/conversations` - Create conversation
- `GET /api/conversations/{id}` - Get conversation
- `DELETE /api/conversations/{id}` - Delete conversation

## Configuration

Set environment variables in `.env`:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=amazon.nova-lite-v1:0
API_HOST=0.0.0.0
API_PORT=8000
```

## Development

```bash
# Install dependencies
uv sync

# Start server with hot reload
uv run uvicorn backend.main:app --reload

# Run tests
uv run python tests/test_server.py
```

For more details, see the [documentation](docs/).
