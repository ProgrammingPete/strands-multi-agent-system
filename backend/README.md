# Canvalo Multi-Agent Backend

FastAPI service providing AI-powered business automation through specialized agents for the Canvalo painting contractor management platform.

## 🤖 Overview

The Canvalo backend is a production-ready FastAPI service that serves as the intelligent core of the business management platform. It provides:

- **Multi-Agent Intelligence**: Supervisor agent orchestrating 9 specialized domain agents
- **Streaming Chat API**: Real-time AI conversations via Server-Sent Events (SSE)
- **Conversation Management**: Full CRUD operations with pagination and context management
- **Production Security**: JWT authentication with Row-Level Security (RLS) enforcement
- **AWS Integration**: Amazon Bedrock for LLM, Secrets Manager for configuration

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    FASTAPI APPLICATION                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  API Layer (backend/main.py)                            │   │
│  │  - REST endpoints with OpenAPI documentation            │   │
│  │  - CORS middleware for frontend integration             │   │
│  │  - Request/response logging and error handling          │   │
│  └─────────────────┬───────────────────────────────────────┘   │
│                    │                                           │
│  ┌─────────────────▼───────────────────────────────────────┐   │
│  │  Service Layer                                           │   │
│  │  - chat_service.py: SSE streaming with agent routing    │   │
│  │  - conversation_service.py: Conversation management     │   │
│  │  - context_manager.py: Context building & summarization │   │
│  │  - auth_middleware.py: JWT validation & user isolation  │   │
│  └─────────────────┬───────────────────────────────────────┘   │
│                    │                                           │
│  ┌─────────────────▼───────────────────────────────────────┐   │
│  │  Agent Layer (../agents/)                               │   │
│  │  - supervisor.py: Intelligent query routing             │   │
│  │  - 9 specialized agents with Supabase CRUD tools       │   │
│  │  - Natural language processing for business operations  │   │
│  └─────────────────┬───────────────────────────────────────┘   │
└──────────────────┼─────────────────────────────────────────────┘
                   │
                   │ Supabase Client
                   │
┌──────────────────▼─────────────────────────────────────────────┐
│                    DATA LAYER                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Supabase PostgreSQL Database                           │   │
│  │  - 9 business entity tables with RLS policies          │   │
│  │  - Conversations and messages tables                    │   │
│  │  - User authentication and session management          │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- **Python 3.13+** (3.11+ supported)
- **uv** package manager
- **Supabase** project with configured database
- **AWS credentials** with Bedrock access

### Installation & Setup

1. **Install dependencies:**
   ```bash
   cd strands-multi-agent-system
   uv sync
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials (see Configuration section)
   ```

3. **Start the server:**
   ```bash
   uv run python -m backend.main
   # Or use the startup script:
   ./start_backend.sh
   ```

4. **Verify installation:**
   ```bash
   curl http://localhost:8000/health
   # Should return: {"status": "healthy", "supabase_configured": true, ...}
   ```

## ⚙️ Configuration

### Development Environment (.env)
```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_PUB_KEY=your-pub-key-here          # For user operations (RLS enforced)
SUPABASE_SERVICE_KEY=your-service-key-here  # For system operations (dev only)

# AWS Configuration
AWS_REGION=us-east-1
AWS_PROFILE=default                         # Optional
BEDROCK_MODEL_ID=amazon.nova-lite-v1:0

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=development

# Testing Configuration
SYSTEM_USER_ID=00000000-0000-0000-0000-000000000000
```

### Production Environment (.env.production)
```bash
# Supabase Configuration (SECURITY CRITICAL)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_PUB_KEY=your-pub-key-here          # Required for user authentication
# SUPABASE_SERVICE_KEY removed in production - SECURITY REQUIREMENT

# AWS Configuration
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=amazon.nova-lite-v1:0

# Production Security
ENVIRONMENT=production
ADMIN_API_KEY=your-secure-admin-key         # Generate with secrets.token_urlsafe(32)

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

**⚠️ Production Security Requirements:**
- **Never include `SUPABASE_SERVICE_KEY`** in production (bypasses RLS)
- **Always set `SUPABASE_PUB_KEY`** (required for JWT validation)
- **Generate secure `ADMIN_API_KEY`** for admin operations
- **Set `ENVIRONMENT=production`** for strict security validation

## 📡 API Endpoints

### Health & Status
```http
GET /                    # Root endpoint with service information
GET /health              # Detailed health check with configuration status
```

### Multi-Agent Chat
```http
POST /api/chat/stream    # Stream AI chat responses via SSE
Content-Type: application/json
Authorization: Bearer <jwt_token>  # Required in production

{
  "message": "What invoices do I have?",
  "conversation_id": "uuid",
  "user_id": "uuid",
  "history": []
}
```

**Response Format (Server-Sent Events):**
```
data: {"type":"token","content":"I can help you","agent_type":"supervisor"}
data: {"type":"token","content":" with invoices","agent_type":"invoices"}
data: {"type":"complete","agent_type":"invoices"}
```

### Conversation Management
```http
GET /api/conversations                    # List user conversations (paginated)
POST /api/conversations                   # Create new conversation
GET /api/conversations/{id}               # Get conversation with messages
DELETE /api/conversations/{id}            # Delete conversation
```

**Query Parameters:**
- `user_id` (required): User ID for authorization
- `limit` (optional): Maximum items to return (default: 50)
- `offset` (optional): Pagination offset (default: 0)

## 🤖 Multi-Agent System

### Supervisor Agent
The supervisor agent (`agents/supervisor.py`) serves as the intelligent router:

- **Query Analysis**: Understands user intent and context
- **Agent Selection**: Routes queries to appropriate specialized agents
- **Response Coordination**: Manages multi-agent interactions
- **Error Handling**: Provides fallback responses and error recovery

### Specialized Agents

| Agent | Domain | Capabilities |
|-------|--------|--------------|
| **Invoices** | Invoice management | Create, view, update invoices; payment tracking; overdue analysis |
| **Appointments** | Scheduling | Calendar management, appointment booking, availability checking |
| **Campaigns** | Marketing | Campaign creation, performance tracking, ROI analysis |
| **Contacts** | CRM | Client/supplier management, communication history, relationship tracking |
| **Goals** | Business objectives | Goal setting, progress tracking, performance analytics |
| **Projects** | Project management | Project lifecycle, status tracking, resource allocation |
| **Proposals** | Estimates/quotes | Proposal creation, approval workflow, conversion tracking |
| **Reviews** | Customer feedback | Review management, sentiment analysis, reputation tracking |
| **Tasks** | Task management | Task assignment, priority management, completion tracking |

### Agent Interaction Examples

```python
# Natural language queries handled by agents:
"Show me all overdue invoices"                    # → Invoices Agent
"Schedule a meeting with John Smith next week"    # → Appointments Agent  
"What's my revenue this month?"                   # → Multiple agents coordination
"Create a project for kitchen repainting"        # → Projects Agent
"Which clients haven't been contacted recently?"  # → Contacts + Analytics
```

## 🔒 Security Architecture

### JWT Authentication
- **Development**: Optional JWT validation for easier testing
- **Production**: Required JWT validation for all API requests
- **User Isolation**: All operations scoped to authenticated user
- **Token Validation**: Supabase JWT signature verification

### Row-Level Security (RLS)
- **Database-Level Security**: PostgreSQL RLS policies on all tables
- **User Data Isolation**: Users can only access their own data
- **Agent Operations**: All agent tools respect RLS policies
- **Admin Operations**: Separate admin authentication for system operations

### Environment-Based Security
```python
# Development mode (relaxed security)
if settings.is_development:
    # Optional JWT validation
    # Service key allowed for system operations
    
# Production mode (strict security)  
if settings.is_production:
    # Required JWT validation
    # Service key forbidden (security risk)
    # Admin API key required for privileged operations
```

## 🧪 Testing

### Unit & Property Tests (No Server Required)
```bash
# Run all unit tests
uv run pytest tests/ --ignore=tests/integration -v

# Run specific test categories
uv run pytest tests/test_foundation.py -v              # Core functionality
uv run pytest tests/test_invoices_agent.py -v         # Agent tests
uv run pytest tests/test_rls_properties.py -v         # Security tests
uv run pytest tests/test_context_manager.py -v        # Context management
```

### Integration Tests (Requires Running Server)
```bash
# Terminal 1: Start the server
uv run python -m backend.main

# Terminal 2: Run integration tests
uv run pytest tests/integration/ -v
```

### Test Coverage
- ✅ **Foundation Tests**: Core functionality and Supabase integration
- ✅ **Agent Tests**: All 9 specialized agents with batch operations
- ✅ **Security Tests**: RLS enforcement and multi-user data isolation
- ✅ **Integration Tests**: End-to-end API testing with real server
- ✅ **Property Tests**: Configuration fallback and error handling
- ✅ **Context Tests**: Token management and conversation context

## 🚀 Deployment

### Docker Deployment (Recommended)
```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY . .
RUN pip install uv && uv sync
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
CMD ["uv", "run", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### AWS ECS Deployment
The backend is designed for deployment on AWS ECS Fargate via the infrastructure project:

- **Container Orchestration**: ECS Fargate with auto-scaling
- **Load Balancing**: Application Load Balancer with health checks
- **Secret Management**: AWS Secrets Manager for runtime configuration
- **Logging**: CloudWatch Logs with structured logging
- **Monitoring**: CloudWatch metrics and alarms

### Environment-Specific Deployment

| Environment | Resources | Security | Features |
|-------------|-----------|----------|----------|
| **Beta** | 0.25 vCPU, 512MB | Development security | Full feature set, test data |
| **Gamma** | 0.5 vCPU, 1GB | Staging security | Production-like, test data |
| **Production** | 1 vCPU, 2GB, auto-scaling | Full security | Live data, monitoring |

## 📊 Performance & Optimization

### Context Management
- **Token Limit Management**: Automatic context truncation for large conversations
- **Context Summarization**: Intelligent summarization of conversation history
- **Message Persistence**: Efficient storage and retrieval of conversation data

### Database Optimization
- **Connection Pooling**: Efficient Supabase connection management
- **Query Optimization**: Indexed queries for conversation and message retrieval
- **Pagination Support**: Efficient handling of large datasets

### Streaming Optimization
- **Token Batching**: Reduced SSE overhead for improved performance
- **Connection Management**: Graceful handling of client disconnections
- **Error Recovery**: Automatic retry logic with exponential backoff

## 📚 Documentation

### Getting Started
- **[Quick Start Guide](docs/QUICK_START.md)** - 5-minute setup guide
- **[API Reference](docs/API_REFERENCE.md)** - Complete endpoint documentation
- **[Security Guide](docs/SECURITY.md)** - Production security implementation

### Implementation Details
- **[Implementation Summary](docs/IMPLEMENTATION_SUMMARY.md)** - Architecture decisions
- **[Context Management](docs/CONTEXT_MANAGEMENT.md)** - Context handling details
- **[Performance Optimization](docs/PERFORMANCE_OPTIMIZATION.md)** - Performance tuning

### Testing & Quality
- **[Tests README](../tests/README.md)** - Comprehensive testing guide
- **[UV Migration Guide](docs/UV_MIGRATION.md)** - Package manager migration

## 🔧 Development

### Project Structure
```
backend/
├── __init__.py              # Package initialization
├── main.py                  # FastAPI application and endpoints
├── config.py                # Configuration management with Pydantic Settings
├── models.py                # Pydantic models for request/response validation
├── chat_service.py          # Chat streaming service with SSE
├── conversation_service.py  # Conversation management with Supabase
├── context_manager.py       # Context building and token management
├── auth_middleware.py       # JWT validation and user authentication
├── admin_auth.py            # Admin authentication for privileged operations
├── error_handler.py         # Error handling with retry logic
└── docs/                    # Comprehensive documentation
```

### Development Workflow

1. **Local Development:**
   ```bash
   # Start with hot reload
   uv run uvicorn backend.main:app --reload --port 8000
   
   # Monitor logs for debugging
   tail -f logs/backend.log
   ```

2. **Testing Changes:**
   ```bash
   # Run unit tests
   uv run pytest tests/ --ignore=tests/integration -v
   
   # Test specific functionality
   curl -X POST http://localhost:8000/api/chat/stream \
     -H "Content-Type: application/json" \
     -d '{"message": "test", "user_id": "test", "conversation_id": "test"}'
   ```

3. **API Documentation:**
   - **Interactive Docs**: http://localhost:8000/docs
   - **ReDoc**: http://localhost:8000/redoc

### Adding New Agents

1. **Create Agent File**: `agents/new_agent.py`
2. **Create Tools File**: `agents/new_agent_tools.py`
3. **Implement Agent Pattern**:
   ```python
   from strands import Agent, tool
   from strands.models import BedrockModel
   
   @tool
   def new_agent_tool(query: str) -> str:
       """Agent description for supervisor routing."""
       agent = Agent(
           model=BedrockModel(model_id=settings.BEDROCK_MODEL_ID),
           system_prompt=SYSTEM_PROMPT,
           tools=[tool1, tool2, tool3]
       )
       return str(agent(query))
   ```
4. **Add to Supervisor**: Update `agents/supervisor.py` tools list
5. **Create Tests**: `tests/test_new_agent.py`

## 🔍 Monitoring & Observability

### Health Checks
```bash
# Basic health check
curl http://localhost:8000/health

# Expected response
{
  "status": "healthy",
  "supabase_configured": true,
  "bedrock_model": "amazon.nova-lite-v1:0",
  "environment": "development",
  "agents_available": 9
}
```

### Logging
- **Structured Logging**: JSON format for production environments
- **Request Tracing**: Unique request IDs for debugging
- **Performance Metrics**: Response times and token usage
- **Error Tracking**: Comprehensive error logging with context

### Metrics to Monitor
- **Request Rate**: Requests per second by endpoint
- **Response Time**: P95/P99 latency for chat streaming
- **Error Rate**: Error percentage by endpoint and error type
- **Token Usage**: LLM token consumption and costs
- **Database Performance**: Query execution times
- **Connection Health**: Supabase and Bedrock connectivity

## 🛠️ Troubleshooting

### Common Issues

**Server won't start:**
```bash
# Check dependencies
uv sync

# Verify environment variables
cat .env | grep -E "(SUPABASE_URL|BEDROCK_MODEL_ID)"

# Check port availability
lsof -i :8000
```

**Authentication errors:**
```bash
# Verify Supabase configuration
curl -H "Authorization: Bearer invalid" http://localhost:8000/api/conversations

# Check JWT token format
echo $JWT_TOKEN | cut -d. -f2 | base64 -d
```

**Agent errors:**
```bash
# Test individual agents
uv run python agents/supervisor.py

# Check AWS credentials
aws bedrock list-foundation-models --region us-east-1
```

### Debug Mode
```python
# Enable debug logging in backend/main.py
import logging
logging.basicConfig(level=logging.DEBUG)

# Or set environment variable
export LOG_LEVEL=DEBUG
```

## 🤝 Contributing

### Code Standards
- **Type Hints**: Use type annotations for all functions
- **Documentation**: Docstrings for all public functions and classes
- **Testing**: Unit tests for new functionality
- **Security**: Follow security best practices and review guidelines

### Pull Request Process
1. **Run Tests**: Ensure all tests pass locally
2. **Update Documentation**: Update relevant documentation
3. **Security Review**: Verify security implications
4. **Performance Impact**: Consider performance implications

## 📄 License

Proprietary - Canvalo Multi-Agent Backend System

---

## 🎯 Quick Links

| Resource | URL | Description |
|----------|-----|-------------|
| **API Docs** | http://localhost:8000/docs | Interactive Swagger documentation |
| **Health Check** | http://localhost:8000/health | Service health and configuration |
| **ReDoc** | http://localhost:8000/redoc | Alternative API documentation |
| **Frontend Integration** | [../CanvaloFrontend/](../CanvaloFrontend/) | React frontend application |
| **Infrastructure** | [../canvalo-infrastructure/](../canvalo-infrastructure/) | AWS CDK deployment |

---

<div align="center">

**🤖 Intelligent Business Automation for Painting Contractors**

*Powered by Strands Agents SDK and Amazon Bedrock*

</div>