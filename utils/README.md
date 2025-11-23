# Supabase Utilities

This directory contains utilities for interacting with Supabase in the multi-agent system.

## Modules

### `supabase_client.py`

Provides a robust Supabase client wrapper with:
- **Singleton pattern** for efficient connection management
- **Automatic retry logic** with exponential backoff (3 attempts by default)
- **Connection pooling** for optimal performance
- **Error handling** with custom exception types
- **Health check** functionality

#### Usage

```python
from utils.supabase_client import get_supabase_client, get_client

# Get the wrapper instance
supabase = get_supabase_client()

# Execute a query with automatic retry
result = supabase.execute_query(
    lambda: supabase.table('invoices').select('*').execute()
)

# Or get the raw client
client = get_client()
result = client.table('invoices').select('*').execute()

# Health check
if supabase.health_check():
    print("Connection is healthy")
```

### `supabase_tools.py`

Provides factory functions to generate Strands tools for CRUD operations:
- `create_get_records_tool()` - Generate a tool for fetching records
- `create_create_record_tool()` - Generate a tool for creating records
- `create_update_record_tool()` - Generate a tool for updating records
- `create_delete_record_tool()` - Generate a tool for deleting records
- `create_crud_toolset()` - Generate a complete CRUD toolset

#### Usage

```python
from utils.supabase_tools import create_crud_toolset
from strands import Agent
from strands.models import BedrockModel

# Create a complete CRUD toolset for invoices
invoice_tools = create_crud_toolset(
    table_name="invoices",
    required_fields=["user_id", "client_id", "amount", "due_date"],
    soft_delete=True  # Use soft delete instead of hard delete
)

# Create an agent with the tools
invoices_agent = Agent(
    model=BedrockModel(model_id="amazon.nova-lite-v1:0"),
    system_prompt="You are an expert in invoice management...",
    tools=[
        invoice_tools['get'],
        invoice_tools['create'],
        invoice_tools['update'],
        invoice_tools['delete']
    ]
)

# Use the agent
response = invoices_agent("Show me all unpaid invoices")
```

#### Individual Tool Creation

```python
from utils.supabase_tools import (
    create_get_records_tool,
    create_create_record_tool,
    create_update_record_tool,
    create_delete_record_tool
)

# Create individual tools with custom configuration
get_projects = create_get_records_tool(
    table_name="projects",
    tool_name="fetch_projects",
    description="Retrieve painting projects",
    default_limit=15,
    max_limit=50
)

create_project = create_create_record_tool(
    table_name="projects",
    required_fields=["user_id", "client_id", "name", "project_type"],
    tool_name="create_new_project"
)

update_project = create_update_record_tool(
    table_name="projects",
    id_field="id"
)

delete_project = create_delete_record_tool(
    table_name="projects",
    soft_delete=True,
    soft_delete_field="deleted_at"
)
```

## Configuration

Set the following environment variables in your `.env` file:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key-here
```

## Error Handling

All tools return JSON strings with consistent error formats:

**Success Response:**
```json
{
  "success": true,
  "data": {...},
  "message": "Operation successful"
}
```

**Error Response:**
```json
{
  "error": "Technical error message",
  "user_message": "User-friendly error message"
}
```

## Features

### Automatic Retry Logic

All database operations automatically retry up to 3 times with exponential backoff:
- Attempt 1: Immediate
- Attempt 2: 1 second delay
- Attempt 3: 2 seconds delay
- Attempt 4: 4 seconds delay (max)

### Connection Pooling

The Supabase client uses connection pooling for optimal performance with concurrent requests.

### Soft Delete Support

Tools can be configured to use soft delete (setting a timestamp) instead of hard delete:

```python
delete_tool = create_delete_record_tool(
    table_name="invoices",
    soft_delete=True,
    soft_delete_field="deleted_at"
)
```

### User Authorization

All tools support user-based authorization through the `user_id` parameter, ensuring users can only access their own data.

### Flexible Filtering

The `get_records` tool supports flexible filtering through JSON:

```python
# Example usage
result = get_invoices(
    user_id="123",
    filters='{"status": "unpaid", "amount_gt": 1000}',
    limit=20,
    order_by="due_date",
    order_desc=True
)
```

## Testing

To test the utilities without Supabase credentials:

```python
# The client will raise SupabaseConnectionError if credentials are missing
from utils.supabase_client import get_supabase_client

try:
    client = get_supabase_client()
    print("Connected successfully")
except Exception as e:
    print(f"Connection failed: {e}")
```

## Next Steps

These utilities will be used to create specialized agents in subsequent tasks:
- Invoices Agent (Task 5)
- Appointments Agent (Task 6)
- Projects Agent (Task 7)
- Proposals Agent (Task 8)
- Contacts Agent (Task 9)
- Reviews Agent (Task 10)
- Campaign Agent (Task 11)
- Tasks Agent (Task 12)
- Settings Agent (Task 13)
