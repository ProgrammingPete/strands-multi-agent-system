# Product Overview

This is a multi-agent AI system built with the Strands Agents SDK that serves as the backend for Canvalo, a painting contractor business management application.

## Purpose
The system provides AI-powered business automation through specialized agents that handle different business domains like invoicing, appointments, projects, and more.

## Architecture
The system uses a Supervisor-Agent pattern:
- **Supervisor Agent**: Routes user queries to the appropriate specialized agent
- **Specialized Agents**: Domain-specific agents (currently Invoices Agent is implemented)

## Backend API
A FastAPI service provides REST endpoints for:
- Streaming chat responses via Server-Sent Events (SSE)
- Conversation management (create, list, get, delete)
- Integration with Supabase for data persistence

## Current Implementation Status
- ✅ Invoices Agent: Invoice creation, viewing, updating, payment tracking
- 🚧 Planned: Appointments, Projects, Proposals, Contacts, Reviews, Campaigns, Tasks, Settings agents

## Integration
- Frontend: React/TypeScript application (CanvaloFrontend)
- Database: Supabase
- LLM: Amazon Bedrock (Nova Lite by default)
