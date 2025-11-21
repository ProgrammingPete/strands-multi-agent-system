# Project Structure

## Root Files
- `main.py`: Main entry point
- `lab.ipynb`: Interactive Jupyter notebook for lab exercises
- `debug_strands.py`: Debugging utilities
- `enable_bedrock_access.py`: AWS Bedrock setup script
- `pyproject.toml`: Python project configuration
- `requirements.txt`: Python dependencies
- `uv.lock`: Dependency lock file
- `.python-version`: Python version specification (3.13)
- `.env`: Environment variables (not in git)
- `.env.example`: Environment template

## Agents Directory (`agents/`)
Contains the specialized agent implementations:

### Active Agents
- `__init__.py`: Package initialization
- `coder.py`: Code generation and file analysis agent
- `alarm_manager.py`: CloudWatch alarm monitoring agent
- `aws_researcher.py`: AWS documentation research agent (uses MCP)
- `aws_manager.py`: AWS resource management agent (DynamoDB, EC2, S3, etc.)
- `orchestrator.py`: Main orchestrator that routes to specialized agents

### Supporting Files
- `run_aws_manager.sh`: Shell script for running AWS manager
- `repl_state/`: Agent REPL state persistence
- `__pycache__/`: Python bytecode cache

## Completed Agents (`completed_agents/`)
Reference implementations with full code:
- `coder_full.py`
- `alarm_manager_full.py`
- `aws_researcher_full.py`
- `aws_manager_agent_full.py`
- `orchestrator_full.py`

## Project Data (`project/`)
Sample data and scripts:
- `flights.csv`: Flight data for DynamoDB
- `flights-schema.csv`: Schema definition
- `userscript.sh`: User script for EC2 instances

## Documentation (`images/`)
Architecture and workflow diagrams:
- `agent.png`: Agent architecture
- `cloudwatch.png`: CloudWatch integration
- `coder.png`: Coder agent workflow
- `web agent.png`: Web agent architecture

## Lab Documentation
- `Creating an AWS DevOps AI Agent with the Strands Agents SDK.md`: Full lab guide
- `Creating an AWS DevOps AI Agent with the Strands Agents SDK.pdf`: PDF version

## State Management
- `repl_state/`: Persistent REPL state
  - `repl_state.pkl`: Pickled state file

## Agent Pattern
Agents follow a consistent pattern:
1. Import necessary tools and models
2. Define system prompt with specific capabilities
3. Create agent with model, prompt, and tools
4. Implement query function decorated with `@tool`
5. Return string response

## Tool Integration
- Agents can be used as tools by other agents via `@tool` decorator
- Orchestrator uses specialized agents as callable tools
- MCP servers provide external tool capabilities (AWS docs, DynamoDB)
