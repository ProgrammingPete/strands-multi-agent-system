# Quick Start Guide - Canvalo Multi-Agent Backend

Get the Canvalo multi-agent FastAPI backend running in 5 minutes.

## Prerequisites

- **Python 3.13+** (3.11+ supported)
- **uv package manager** ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))
- **Supabase project** with configured database
- **AWS credentials** with Bedrock access

## Configuration

### Development Environment

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your credentials:
   ```bash
   # Required for Supabase
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_PUB_KEY=your-pub-key-here      # For user operations (RLS enforced)
   SUPABASE_SERVICE_KEY=your-service-key-here # For system operations (dev only)
   
   # Required for AI agents
   AWS_REGION=us-east-1
   BEDROCK_MODEL_ID=amazon.nova-lite-v1:0
   
   # Environment configuration
   ENVIRONMENT=development
   SYSTEM_USER_ID=00000000-0000-0000-0000-000000000000
   
   # Optional - API configuration
   API_HOST=0.0.0.0
   API_PORT=8000
   ```

### Production Environment

For production, use `.env.production.example` as a template:
```bash
cp .env.production.example .env
```

**Important Production Security Requirements:**
- Do NOT include `SUPABASE_SERVICE_KEY` (bypasses RLS security)
- Must include `SUPABASE_PUB_KEY` (required for user authentication)
- Set `ENVIRONMENT=production`
- Set `ADMIN_API_KEY` for admin operations (generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"`)

See [SECURITY.md](SECURITY.md) for detailed security configuration.

## Running the Server

### Option 1: Using the startup script
```bash
./start_backend.sh
```

### Option 2: Using uv directly
```bash
uv run python -m backend.main
```

### Option 3: Using uvicorn with uv
```bash
uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

## Testing the Server

### 1. Health Check
```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00Z",
  "supabase_configured": true,
  "bedrock_model": "amazon.nova-lite-v1:0",
  "environment": "development",
  "agents_available": 9
}
```

### 2. Test Multi-Agent Chat
```bash
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What can you help me with?",
    "conversation_id": "test-123",
    "user_id": "00000000-0000-0000-0000-000000000000",
    "history": []
  }'
```

**Expected Response (SSE Stream):**
```
data: {"type":"token","content":"I can help you","agent_type":"supervisor"}
data: {"type":"token","content":" manage your painting business","agent_type":"supervisor"}
data: {"type":"token","content":" with 9 specialized agents","agent_type":"supervisor"}
data: {"type":"complete","agent_type":"supervisor","tokens_used":25}
```

### 3. Test Specific Agent
```bash
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Show me all my invoices",
    "conversation_id": "test-124", 
    "user_id": "00000000-0000-0000-0000-000000000000",
    "history": []
  }'
```

### 4. Test Conversation Management
```bash
# Create conversation
curl -X POST http://localhost:8000/api/conversations \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "00000000-0000-0000-0000-000000000000",
    "title": "Test Conversation"
  }'

# List conversations
curl "http://localhost:8000/api/conversations?user_id=00000000-0000-0000-0000-000000000000"
```

### 5. Run Automated Tests
```bash
# Unit tests (no server required)
uv run pytest tests/ --ignore=tests/integration -v

# Integration tests (requires running server)
uv run pytest tests/integration/ -v
```

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Common Issues

### Issue: "Missing required environment variables"
**Solution**: Make sure `.env` file exists and contains `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`

### Issue: "Connection refused"
**Solution**: Make sure the server is running on port 8000

### Issue: "Module not found"
**Solution**: Run `uv sync` to install dependencies

### Issue: "AWS credentials not found"
**Solution**: Configure AWS credentials or set AWS environment variables

## Development Tips

### Enable debug logging
```python
# In backend/main.py
logging.basicConfig(level=logging.DEBUG)
```

### Hot reload
The server automatically reloads when you change code files (when using `--reload` flag)

### Test individual endpoints
Use the Swagger UI at http://localhost:8000/docs for interactive testing

### Monitor logs
Watch the console output for request/response logs and errors

## Production Deployment

### Security Checklist

Before deploying to production:
- [ ] Remove `SUPABASE_SERVICE_KEY` from environment
- [ ] Set `SUPABASE_PUB_KEY` for user authentication
- [ ] Set `ENVIRONMENT=production`
- [ ] Generate and set `ADMIN_API_KEY` for admin operations
- [ ] Configure CORS origins for your production domain
- [ ] Enable HTTPS/TLS

### Using Docker
```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY . .
RUN pip install uv && uv sync
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t canvalo-backend .
# Use production env file (without SUPABASE_SERVICE_KEY)
docker run -p 8000:8000 --env-file .env.production canvalo-backend
```

### Using systemd
Create `/etc/systemd/system/canvalo-backend.service`:
```ini
[Unit]
Description=Canvalo Backend Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/canvalo
ExecStart=/usr/local/bin/uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable canvalo-backend
sudo systemctl start canvalo-backend
```

## Next Steps

1. Configure Supabase database with required tables (see design.md)
2. Implement remaining specialized agents (Tasks 6-13)
3. Integrate with frontend (Task 18-20)
4. Run end-to-end tests (Task 22)
5. Deploy to production (Task 26-28)

## Support

For issues or questions:
- Check the logs in the console
- Review `backend/README.md` for detailed documentation
- Check `backend/IMPLEMENTATION_SUMMARY.md` for architecture details
