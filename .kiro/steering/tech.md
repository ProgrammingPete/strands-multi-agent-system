# Technology Stack

## Python Environment
- **Python Version**: 3.11+ (3.13 recommended)
- **Package Manager**: uv
- **Virtual Environment**: `.venv/`

## Core Framework
- **strands-agents** (>=1.13.0): Multi-agent framework
- **strands-agents-tools** (>=0.2.12): Built-in agent tools
- **FastAPI** (>=0.115.0): REST API framework
- **uvicorn** (>=0.32.0): ASGI server
- **Pydantic** (>=2.10.0): Data validation
- **pydantic-settings** (>=2.6.0): Settings management

## Database & Backend
- **Supabase** (>=2.0.0): Backend-as-a-Service for data persistence
- **boto3** (>=1.40.61): AWS SDK for Bedrock access

## AI/LLM
- **Amazon Bedrock**: LLM provider
- **Default Model**: `amazon.nova-lite-v1:0`
- **Alternative Models**: Nova Pro, Claude Haiku 3.5

## Development Tools
- **pytest** (>=9.0.1): Testing framework
- **pytest-asyncio** (>=1.3.0): Async test support
- **python-dotenv** (>=1.2.1): Environment variable management

## Configuration
Environment variables (`.env`):
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_SERVICE_KEY`: Supabase service role key
- `AWS_REGION`: AWS region (default: us-east-1)
- `AWS_PROFILE`: Optional AWS profile name
- `BEDROCK_MODEL_ID`: Bedrock model ID
- `API_HOST`: API host (default: 0.0.0.0)
- `API_PORT`: API port (default: 8000)

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
uv run pytest tests/         # Run all tests
uv run pytest tests/ -v      # Verbose output
```

### Running Agents Directly
```bash
uv run python agents/supervisor.py    # Run supervisor agent
uv run python agents/invoices_agent.py # Run invoices agent
```
