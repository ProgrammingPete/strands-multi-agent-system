# Product Overview

This is a multi-agent AI system built with the Strands Agents SDK that serves as the backend for Canvalo, a painting contractor business management application.

## Purpose
The system provides AI-powered business automation through specialized agents that handle different business domains like invoicing, appointments, projects, and more.

## Architecture
The system uses a Supervisor-Agent pattern:
- **Supervisor Agent**: Routes user queries to the appropriate specialized agent
- **Specialized Agents**: Domain-specific agents with Supabase tools

## Backend API
A FastAPI service provides REST endpoints for:
- Streaming chat responses via Server-Sent Events (SSE)
- Conversation management (create, list, get, delete) with pagination
- JWT authentication (required in production, optional in development)
- Integration with Supabase for data persistence

## Security Features
- JWT token validation for authenticated requests
- User ID verification against JWT claims
- Row-Level Security (RLS) enforcement via Supabase
- Environment-based auth enforcement (strict in production)
- Admin authentication for service-level operations
- Structured error responses with user-friendly messages

## Current Implementation Status
### Implemented Tools
- ✅ Invoices: Invoice creation, viewing, updating, payment tracking
- ✅ Appointments: Scheduling and calendar management
- ✅ Campaigns: Marketing campaign management
- ✅ Contacts: Client/supplier CRM
- ✅ Goals: Business goal tracking
- ✅ Projects: Project management
- ✅ Proposals: Estimates and proposals
- ✅ Reviews: Customer review management
- ✅ Tasks: Task tracking

### Testing
- ✅ Unit tests for core functionality
- ✅ E2E integration tests
- ✅ RLS property-based tests
- ✅ Context management tests

## Integration
- Frontend: React/TypeScript application (CanvaloFrontend)
- Database: Supabase with Row-Level Security
- LLM: Amazon Bedrock (Nova Lite by default)
