# Project Structure

## Root Files
- `pyproject.toml`: Python project configuration (uv package manager)
- `requirements.txt`: Python dependencies
- `.env`: Environment variables (Supabase, AWS, Bedrock config)
- `start_backend.sh`: Script to start the FastAPI backend
- `run_tests.sh`: Script to run the test suite

## Backend Directory (`backend/`)
FastAPI service for the multi-agent chat system:

- `main.py`: FastAPI app with endpoints for chat streaming and conversation management
- `config.py`: Pydantic settings loaded from environment variables
- `models.py`: Pydantic models for requests/responses (ChatRequest, Message, StreamChunk, etc.)
- `chat_service.py`: Handles streaming chat responses using the supervisor agent
- `conversation_service.py`: Manages conversations in Supabase
- `context_manager.py`: Manages conversation context
- `auth_middleware.py`: JWT authentication middleware for Supabase auth
- `admin_auth.py`: Admin authentication for service-level operations
- `error_handler.py`: Error handling utilities

### Backend Documentation (`backend/docs/`)
- `INDEX.md`: Documentation index
- `API_REFERENCE.md`: API endpoint documentation
- `SECURITY.md`: Security implementation details
- `QUICK_START.md`: Getting started guide
- `CONTEXT_MANAGEMENT.md`: Context handling documentation
- `PERFORMANCE_OPTIMIZATION.md`: Performance tuning guide

### API Endpoints
- `GET /`: Root health check
- `GET /health`: Detailed health check
- `POST /api/chat/stream`: Stream chat response (SSE) with JWT auth
- `GET /api/conversations`: List user conversations (paginated)
- `POST /api/conversations`: Create conversation
- `GET /api/conversations/{id}`: Get conversation with messages (paginated)
- `DELETE /api/conversations/{id}`: Delete conversation

### Authentication
- JWT validation via `Authorization: Bearer <token>` header
- Required in production, optional in development
- User ID verification against JWT claims
- Admin auth for service-level operations

## Agents Directory (`agents/`)
Strands agent implementations:

### Core Agents
- `supervisor.py`: Main orchestrator that routes to specialized agents
- `invoices_agent.py`: Invoice management agent

### Domain Tools (Supabase CRUD operations)
- `invoice_tools.py`: Invoice operations
- `appointment_tools.py`: Appointment scheduling
- `campaign_tools.py`: Marketing campaigns
- `contact_tools.py`: Client/supplier contacts
- `goal_tools.py`: Business goals
- `project_tools.py`: Project management
- `proposal_tools.py`: Estimates and proposals
- `review_tools.py`: Customer reviews
- `task_tools.py`: Task management
- `tool_utils.py`: Shared utilities for tools

### Agent Pattern
1. Define system prompt with capabilities and guidelines
2. Create BedrockModel with model ID from settings
3. Define tools using `@tool` decorator
4. Create Agent with model, prompt, and tools
5. Expose as tool for supervisor using `@tool` decorator

## Tests Directory (`tests/`)
Comprehensive test suite:

### Test Files
- `conftest.py`: Pytest fixtures and configuration
- `test_foundation.py`: Core functionality tests
- `test_server.py`: API endpoint tests
- `test_e2e.py`: End-to-end integration tests
- `test_context_manager.py`: Context management tests
- `test_invoices_agent.py`: Invoice agent tests
- `test_invoices_agent_batch.py`: Batch invoice tests
- `test_rls_properties.py`: Row-Level Security property tests
- `test_cleanup.py`: Test data cleanup utilities

### Verification Scripts
- `verify_integration.py`: Integration verification
- `verify_supabase_key.py`: Supabase key validation
- `verify_context_manager.py`: Context manager verification

## Common Commands

### Start Backend
```bash
uv run python -m backend.main
# Or use uvicorn directly:
uv run uvicorn backend.main:app --reload --port 8000
```

### Run Tests
```bash
uv run pytest tests/                    # Run all tests
uv run pytest tests/ -v                 # Verbose output
uv run pytest tests/test_e2e.py         # Run specific test file
uv run pytest tests/ -k "test_name"     # Run tests matching pattern
```
