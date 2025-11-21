# Product Overview

This is a multi-agent AI system built with the Strands Agents SDK for AWS DevOps automation. The system demonstrates how to create specialized AI agents that work together to handle complex AWS operational workflows.

## Purpose
The project serves as a lab/tutorial for building AWS DevOps AI agents that can:
- Monitor AWS infrastructure health via CloudWatch alarms
- Research AWS documentation and best practices
- Generate and execute code
- Manage AWS resources (EC2, DynamoDB, S3, etc.)
- Orchestrate complex multi-step operations through natural language

## Use Case
Designed for AnyCompany Airlines scenario - automating DevOps operations for a multi-cloud infrastructure, reducing manual effort in monitoring, provisioning, and responding to operational issues.

## Agent Architecture
The system uses an "Agents as Tools" pattern with:
- **Orchestrator Agent**: Routes requests to specialized agents
- **Specialized Agents**:
  - Coder: File analysis and code generation
  - Alarm Manager: CloudWatch monitoring
  - AWS Researcher: Documentation lookup via MCP
  - AWS Manager: Resource provisioning and management

## Key Features
- Integration with Amazon Bedrock (Nova Lite, Nova Pro, Claude Haiku 3.5)
- Model Context Protocol (MCP) for AWS documentation access
- DynamoDB MCP for database operations
- Natural language to AWS operations translation
