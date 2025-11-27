# Project Structure

## Root Files
- `pyproject.toml`: Python project configuration (uv package manager)
- `requirements.txt`: Python dependencies
- `.env`: Environment variables (Supabase, AWS, Bedrock config)
- `start_backend.sh`: Script to start the FastAPI backend

## Backend Directory (`backend/`)
FastAPI service for the multi-agent chat system:

- `main.py`: FastAPI app with endpoints for chat streaming and conversation management
- `config.py`: Pydantic settings loaded from environment variables
- `models.py`: Pydantic models for requests/responses (ChatRequest, Message, StreamChunk, etc.)
- `chat_service.py`: Handles streaming chat responses using the supervisor agent
- `conversation_service.py`: Manages conversations in Supabase
- `context_manager.py`: Manages conversation context
- `error_handler.py`: Error handling utilities

### API Endpoints
- `POST /api/chat/stream`: Stream chat response (SSE)
- `GET /api/conversations`: List user conversations
- `POST /api/conversations`: Create conversation
- `GET /api/conversations/{id}`: Get conversation with messages
- `DELETE /api/conversations/{id}`: Delete conversation

## Agents Directory (`agents/`)
Strands agent implementations:

- `supervisor.py`: Main orchestrator that routes to specialized agents
- `invoices_agent.py`: Invoice management agent (create, view, update, delete)
- `invoice_tools.py`: Supabase tools for invoice CRUD operations

### Agent Pattern
1. Define system prompt with capabilities and guidelines
2. Create BedrockModel with model ID from settings
3. Define tools using `@tool` decorator
4. Create Agent with model, prompt, and tools
5. Expose as tool for supervisor using `@tool` decorator

## Tests Directory (`tests/`)
Pytest test files for backend and agents.

## Common Commands

### Start Backend
```bash
uv run python -m backend.main
# Or use uvicorn directly:
uv run uvicorn backend.main:app --reload --port 8000
```

### Run Tests
```bash
uv run pytest tests/
```
