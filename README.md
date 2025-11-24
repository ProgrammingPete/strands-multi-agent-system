# Canvalo Multi-Agent System

A sophisticated multi-agent AI system built with the Strands Agents SDK for managing painting contractor business operations through natural language conversations.

## Overview

This system integrates specialized AI agents into Canvalo's business management platform, enabling users to manage invoices, appointments, projects, proposals, contacts, reviews, campaigns, tasks, and settings through conversational AI.

## Architecture

The system uses an "Agents as Tools" pattern with:
- **Supervisor Agent**: Routes user queries to appropriate specialized agents
- **Specialized Agents**: Domain experts for different business functions
  - Invoices Agent ✅
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
├── utils/                     # Utility modules
│   ├── supabase_client.py    # Supabase client wrapper
│   └── supabase_tools.py     # Generic CRUD tool generators
├── tests/                     # Test suite
│   ├── test_foundation.py    # Foundation tests
│   ├── test_invoices_agent.py # Invoices agent tests
│   ├── run_all_tests.py      # Test runner
│   └── README.md             # Testing documentation
├── .kiro/                     # Kiro IDE specifications
│   └── specs/
│       └── multi-agent-chat/ # Feature specifications
└── .env                       # Environment configuration
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
```
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_service_key
AWS_REGION=us-east-1
AWS_PROFILE=default
```

## Usage

### Running the Supervisor Agent

```bash
python -m agents.supervisor
```

This starts an interactive session where you can chat with the supervisor agent, which will route your queries to the appropriate specialized agents.

### Running Individual Agents

```bash
# Test the invoices agent directly
python -m agents.invoices_agent
```

## Testing

### Run All Tests

```bash
# Using the convenience script
./run_tests.sh

# Or directly
python tests/run_all_tests.py
```

### Run Specific Tests

```bash
# Run foundation tests only
python tests/run_all_tests.py --test foundation

# Run invoices tests only
python tests/run_all_tests.py --test invoices
```

### Verbose Output

```bash
python tests/run_all_tests.py --verbose
```

### Run Individual Test Module

```bash
python tests/test_foundation.py
python tests/test_invoices_agent.py
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

- **Phase 1 Foundation**
  - Supervisor agent with routing logic
  - Supabase client wrapper with retry logic
  - Generic CRUD tool generators
  - Comprehensive test suite

- **Invoices Agent**
  - Create, read, update, delete invoices
  - Payment tracking
  - Status management
  - Professional formatting

### In Progress 🔄

- Additional specialized agents (appointments, projects, etc.)
- Frontend integration
- Streaming responses
- Voice mode support

### Planned 📋

- Analytics integration
- Multi-agent coordination
- Context management
- Error recovery
- Performance optimization

## Documentation

- [Design Document](.kiro/specs/multi-agent-chat/design.md)
- [Requirements](.kiro/specs/multi-agent-chat/requirements.md)
- [Implementation Tasks](.kiro/specs/multi-agent-chat/tasks.md)
- [Testing Guide](tests/README.md)

## Contributing

1. Follow the established agent pattern
2. Write tests for new features
3. Update documentation
4. Ensure all tests pass before committing

## License

[Add license information]

## Support

For issues or questions, please [add contact information or issue tracker link].
