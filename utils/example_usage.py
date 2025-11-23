"""
Example usage of Supabase utilities and CRUD tool generators.

This file demonstrates how to use the Supabase client wrapper and
CRUD tool generators to create tools for specialized agents.
"""

from supabase_tools import (
    create_get_records_tool,
    create_create_record_tool,
    create_update_record_tool,
    create_delete_record_tool,
    create_crud_toolset
)

# Example 1: Create individual tools for invoices
get_invoices = create_get_records_tool(
    table_name="invoices",
    description="Fetch invoices from the database with optional filters"
)

create_invoice = create_create_record_tool(
    table_name="invoices",
    required_fields=["user_id", "client_id", "amount", "due_date"]
)

update_invoice = create_update_record_tool(
    table_name="invoices"
)

delete_invoice = create_delete_record_tool(
    table_name="invoices",
    soft_delete=True  # Use soft delete for invoices
)

# Example 2: Create a complete CRUD toolset for appointments
appointment_tools = create_crud_toolset(
    table_name="appointments",
    required_fields=["user_id", "client_id", "scheduled_at", "location"],
    default_limit=20,
    max_limit=100,
    soft_delete=False
)

# Access individual tools from the toolset
get_appointments = appointment_tools['get']
create_appointment = appointment_tools['create']
update_appointment = appointment_tools['update']
delete_appointment = appointment_tools['delete']

# Example 3: Create tools for projects with custom configuration
get_projects = create_get_records_tool(
    table_name="projects",
    tool_name="fetch_projects",
    description="Retrieve painting projects with filtering and sorting",
    default_limit=15,
    max_limit=50
)

create_project = create_create_record_tool(
    table_name="projects",
    required_fields=["user_id", "client_id", "name", "project_type", "start_date"],
    tool_name="create_new_project"
)

# Example 4: Usage in an agent
"""
from strands import Agent
from strands.models import BedrockModel

# Create an invoices agent with CRUD tools
invoices_agent = Agent(
    model=BedrockModel(model_id="amazon.nova-lite-v1:0"),
    system_prompt="You are an expert in invoice management...",
    tools=[
        get_invoices,
        create_invoice,
        update_invoice,
        delete_invoice
    ]
)

# Query the agent
response = invoices_agent("Show me all unpaid invoices for user 123")
"""

if __name__ == "__main__":
    print("Supabase utilities example usage")
    print("=" * 50)
    print("\nThis file demonstrates how to create CRUD tools for Supabase tables.")
    print("\nExample tools created:")
    print("  - get_invoices")
    print("  - create_invoice")
    print("  - update_invoice")
    print("  - delete_invoice")
    print("  - appointment_tools (complete CRUD toolset)")
    print("  - get_projects, create_project")
    print("\nThese tools can be used with Strands agents to interact with Supabase.")
