# Technology Stack

## Python Environment
- **Python Version**: 3.13 (specified in `.python-version`)
- **Package Manager**: uv (modern Python package manager)
- **Virtual Environment**: `.venv/` directory

## Core Dependencies
- **strands-agents** (>=1.13.0): Main agent framework
- **strands-agents-tools** (>=0.2.12): Built-in tools for agents
- **boto3** (>=1.40.61): AWS SDK for Python
- **python-dotenv** (>=1.2.1): Environment variable management
- **mcp** (>=1.19.0): Model Context Protocol implementation

## Development Tools
- **jupyter** (>=1.1.1): Interactive notebook environment
- **ipywidgets** (>=8.1.7): Jupyter widgets
- **ddgs** (>=9.6.1): DuckDuckGo search integration

## AWS Integration
- **Amazon Bedrock**: LLM access (Nova Lite, Nova Pro, Claude Haiku 3.5)
- **IAM**: Requires `bedrock:InvokeModelWithResponseStream` permission
- **CloudWatch**: Alarm monitoring
- **DynamoDB**: Database operations via MCP
- **EC2, S3**: Resource management

## MCP Servers
- **AWS Documentation MCP**: Real-time AWS docs access
- **DynamoDB MCP**: Database operations
- Uses `uvx` for running MCP servers (stdio client)

## Project Management
- **pyproject.toml**: Modern Python project configuration
- **requirements.txt**: Legacy dependency list
- **uv.lock**: Dependency lock file

## Common Commands

### Environment Setup
```bash
source .venv/bin/activate    # Activate virtual environment
uv sync                      # Install dependencies with uv
pip install -r requirements.txt  # Alternative: install with pip
```

### Running Agents
```bash
python -u agents/coder.py           # Run coder agent
python -u agents/alarm_manager.py   # Run alarm manager
python -u agents/aws_researcher.py  # Run AWS researcher
python -u agents/aws_manager.py     # Run AWS manager
python -u agents/orchestrator.py    # Run orchestrator
```

### Development
```bash
jupyter notebook lab.ipynb   # Open lab notebook
python main.py              # Run main entry point
python debug_strands.py     # Debug utilities
```

### AWS Setup
```bash
python enable_bedrock_access.py  # Configure Bedrock access
```

## Configuration
- `.env`: Environment variables (AWS credentials, region, etc.)
- `.env.example`: Template for environment configuration
