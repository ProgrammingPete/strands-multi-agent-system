# Technology Stack

## Python Environment
- **Python Version**: 3.11+ (3.13 recommended)
- **Package Manager**: uv
- **Virtual Environment**: `.venv/`

## Core Framework
- **strands-agents**: Multi-agent framework
- **strands-agents-tools**: Built-in agent tools
- **FastAPI**: REST API framework
- **uvicorn**: ASGI server
- **Pydantic**: Data validation
- **pydantic-settings**: Settings management

## Database & Backend
- **Supabase**: Backend-as-a-Service for data persistence
- **boto3**: AWS SDK for Bedrock access

## AI/LLM
- **Amazon Bedrock**: LLM provider
- **Default Model**: `amazon.nova-lite-v1:0`
- **Alternative Models**: Nova Pro, Claude Haiku 3.5

## Development Tools
- **pytest**: Testing framework
- **pytest-asyncio**: Async test support
- **python-dotenv**: Environment variable management

## Configuration
Environment variables (`.env`):
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_SERVICE_KEY`: Supabase service role key
- `SUPABASE_PUB_KEY`: Supabase anonymous key (for JWT validation)
- `AWS_REGION`: AWS region (default: us-east-1)
- `AWS_PROFILE`: Optional AWS profile name
- `BEDROCK_MODEL_ID`: Bedrock model ID
- `API_HOST`: API host (default: 0.0.0.0)
- `API_PORT`: API port (default: 8000)
- `ENVIRONMENT`: Environment mode (`development` or `production`)
- `SYSTEM_USER_ID`: System user ID for testing

## Common Commands

### Environment Setup
```bash
uv sync                      # Install dependencies
```

### Running the Backend
```bash
uv run python -m backend.main                           # Start FastAPI server
uv run uvicorn backend.main:app --reload --port 8000    # Alternative with hot reload
```

### Testing
```bash
# Unit & property tests (no server required)
uv run pytest tests/ --ignore=tests/integration -v

# Integration tests (requires running server)
uv run pytest tests/integration/ -v

# All tests
uv run pytest tests/ -v
```

### Running Agents Directly
```bash
uv run python agents/supervisor.py    # Run supervisor agent
uv run python agents/invoices_agent.py # Run invoices agent
```
