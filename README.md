# Canvalo Multi-Agent System

A sophisticated multi-agent AI system built with the Strands Agents SDK for managing painting contractor business operations through natural language conversations.

## Overview

This system integrates specialized AI agents into Canvalo's business management platform, enabling users to manage invoices, appointments, projects, proposals, contacts, reviews, campaigns, tasks, and settings through conversational AI.

## Architecture

The system uses an "Agents as Tools" pattern with:
- **Supervisor Agent**: Routes user queries to appropriate specialized agents
- **Specialized Agents**: Domain experts with Supabase CRUD tools
  - Invoices ✅
  - Appointments Agent (planned)
  - Projects Agent (planned)
  - Proposals Agent (planned)
  - Contacts Agent (planned)
  - Reviews Agent (planned)
  - Campaign Agent (planned)
  - Tasks Agent (planned)
  - Settings Agent (planned)

## Technology Stack

- **Python**: 3.13
- **Agent Framework**: Strands Agents SDK (>=1.13.0)
- **LLM**: Amazon Bedrock (Nova Lite/Pro, Claude Haiku 3.5)
- **Database**: Supabase (PostgreSQL)
- **Package Manager**: uv

## Project Structure

```
strands-multi-agent-system/
├── agents/                    # Agent implementations
│   ├── supervisor.py         # Main supervisor agent
│   ├── invoices_agent.py     # Invoice management agent
│   ├── invoice_tools.py      # Invoice CRUD tools
│   └── ...                   # Additional agents (to be added)
├── backend/                   # FastAPI backend service ✅
│   ├── main.py               # FastAPI application
│   ├── chat_service.py       # Chat streaming service
│   ├── conversation_service.py # Conversation management
│   ├── context_manager.py    # Context management
│   ├── config.py             # Configuration
│   ├── models.py             # Pydantic models
│   ├── error_handler.py      # Error handling
│   ├── docs/                 # Backend documentation
│   └── README.md             # Backend overview
├── utils/                     # Utility modules
│   ├── supabase_client.py    # Supabase client wrapper
│   ├── supabase_tools.py     # Generic CRUD tool generators
│   ├── example_usage.py      # Usage examples
│   └── README.md             # Utils documentation
├── tests/                     # Test suite
│   ├── test_foundation.py    # Foundation tests
│   ├── test_invoices_agent.py # Invoices agent tests
│   ├── test_invoices_agent_batch.py # Batch invoices tests
│   ├── test_context_manager.py # Context manager tests
│   ├── test_config_secrets_property.py # Config property tests
│   ├── test_rls_properties.py # RLS property tests
│   ├── integration/          # Integration tests (require running server)
│   │   ├── test_server.py    # Server endpoint tests
│   │   └── test_e2e.py       # End-to-end tests
│   ├── verify_*.py           # Verification scripts
│   ├── run_all_tests.py      # Test runner
│   ├── docs/                 # Test documentation
│   └── README.md             # Testing documentation
├── .kiro/                     # Kiro IDE specifications
│   └── specs/                # Feature specifications
├── start_backend.sh          # Backend startup script
├── run_tests.sh              # Test runner script
└── .env                      # Environment configuration
```

## Setup

### Prerequisites

- Python 3.13+
- uv package manager
- AWS credentials with Bedrock access
- Supabase project and credentials

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd strands-multi-agent-system
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows
```

3. Install dependencies:
```bash
uv sync
# or
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your credentials
```

Required environment variables:
```bash
# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key        # For user operations (RLS enforced)
SUPABASE_SERVICE_KEY=your_service_key  # For system operations (dev only)

# AWS Configuration
AWS_REGION=us-east-1
AWS_PROFILE=default
AWS_BEARER_TOKEN_BEDROCK=your-bedrock-token-here

# Environment Configuration
ENVIRONMENT=development                 # Set to 'production' for production
SYSTEM_USER_ID=00000000-0000-0000-0000-000000000000  # For testing
```

**Production Note:** In production, do NOT include `SUPABASE_SERVICE_KEY` as it bypasses Row Level Security. See [Security Guide](backend/docs/SECURITY.md) for details.

## Usage

### Running the FastAPI Backend Server

```bash
# Quick start
./start_backend.sh

# Or manually
uv run python -m backend.main
```

The backend provides REST API endpoints for chat streaming and conversation management. See [backend/docs/](backend/docs/) for full documentation.

### Running the Supervisor Agent (CLI)

```bash
uv run python -m agents.supervisor
```

This starts an interactive session where you can chat with the supervisor agent, which will route your queries to the appropriate specialized agents.

### Running Individual Agents

```bash
# Test the invoices agent directly
uv run python -m agents.invoices_agent
```

## Testing

### Run Unit & Property Tests (No Server Required)

```bash
# Run all unit and property tests
uv run pytest tests/ --ignore=tests/integration -v

# Run specific test file
uv run pytest tests/test_foundation.py -v

# Run with pattern matching
uv run pytest tests/ --ignore=tests/integration -k "config" -v
```

### Run Integration Tests (Requires Running Server)

```bash
# Terminal 1: Start the server
uv run python -m backend.main

# Terminal 2: Run integration tests
uv run pytest tests/integration/ -v
```

### Run All Tests

```bash
# Using pytest (server must be running for integration tests)
uv run pytest tests/ -v

# Using the convenience script
./run_tests.sh
```

See [tests/README.md](tests/README.md) for detailed testing documentation.

## Development

### Adding a New Agent

1. Create agent file: `agents/<agent_name>_agent.py`
2. Create tools file: `agents/<agent_name>_tools.py`
3. Implement agent with system prompt and tools
4. Add agent to supervisor's tools list
5. Create test file: `tests/test_<agent_name>_agent.py`
6. Run tests to verify implementation

Example structure:
```python
# agents/example_agent.py
from strands import Agent, tool
from strands.models import BedrockModel
from .example_tools import get_items, create_item

@tool
def example_agent_tool(query: str) -> str:
    """Agent description."""
    agent = Agent(
        model=BedrockModel(model_id="amazon.nova-lite-v1:0"),
        system_prompt=SYSTEM_PROMPT,
        tools=[get_items, create_item]
    )
    return str(agent(query))
```

### Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Include docstrings for all functions and classes
- Add logging for debugging
- Handle errors gracefully with user-friendly messages

## Features

### Implemented ✅

- **All Domain Agents**
  - Invoices: Create, read, update, delete, payment tracking
  - Appointments: Scheduling and calendar management
  - Projects: Project tracking and management
  - Proposals: Estimates and proposals
  - Contacts: Client/supplier CRM
  - Reviews: Customer review management
  - Campaigns: Marketing campaigns
  - Tasks: Task tracking
  - Goals: Business goal tracking

- **FastAPI Backend Service**
  - REST API with streaming chat and conversation management
  - Server-Sent Events (SSE) for real-time responses
  - JWT authentication (required in production)
  - CORS support for frontend integration

- **Security**
  - JWT token validation via Supabase
  - Row-Level Security (RLS) enforcement
  - User-scoped database operations
  - Admin authentication for service operations

- **AWS Deployment Ready**
  - Dockerfile with health checks
  - Secrets Manager integration with .env fallback
  - CDK infrastructure in separate repo (canvalo-infrastructure)

### In Progress 🔄

- Rate limiting
- Audit logging
- Voice mode support

### Planned 📋

- Analytics integration
- CloudWatch alarms and dashboards
- CI/CD pipeline via CDK Pipelines

## Documentation

### Specifications
- [Design Document](.kiro/specs/multi-agent-chat/design.md)
- [Requirements](.kiro/specs/multi-agent-chat/requirements.md)
- [Implementation Tasks](.kiro/specs/multi-agent-chat/tasks.md)

### Guides
- [Testing Guide](tests/README.md)
- [Backend Documentation](backend/docs/) - FastAPI service documentation
  - [Quick Start](backend/docs/QUICK_START.md)
  - [Full API Reference](backend/docs/README.md)
  - [Security Guide](backend/docs/SECURITY.md)
  - [Implementation Summary](backend/docs/IMPLEMENTATION_SUMMARY.md)
- [Database Migrations](migrations/README.md) - Schema migration instructions

## Contributing

1. Follow the established agent pattern
2. Write tests for new features
3. Update documentation
4. Ensure all tests pass before committing

## License

[Add license information]

## Support

For issues or questions, please [add contact information or issue tracker link].
