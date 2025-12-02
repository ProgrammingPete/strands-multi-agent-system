"""
Supervisor Agent - Main orchestrator for routing queries to specialized agents.

This agent analyzes user queries and routes them to the appropriate specialized agent.
It extracts user context from the environment and passes it to all agent invocations.
"""

import logging
import os
from strands import Agent
from strands.models import BedrockModel

from backend.config import settings

# Import specialized agents
from .invoices_agent import invoices_agent_tool

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.getLogger('strands').setLevel(logging.INFO)

logger = logging.getLogger(__name__)

bedrock_model = BedrockModel(
    model_id=settings.bedrock_model_id,
    max_tokens=4096
)

SUPERVISOR_SYSTEM_PROMPT = """
You are the Supervisor Agent for Canvalo, a painting contractor business management system.
Your role is to analyze user queries and route them to the appropriate specialized agent.

IMPORTANT: When calling any agent tool, you MUST extract the User ID from the system context
provided at the start of the conversation (in the format [SYSTEM: User ID is <uuid>]) and
pass it to the agent tool. This is required for proper data isolation and security.

IMPLEMENTED AGENTS (you can use these):
- Invoices Agent: Handles invoice creation, viewing, updating, and payment tracking
  - When calling invoices_agent_tool, pass the user_id parameter

NOT YET IMPLEMENTED (do NOT use or hallucinate data for these):
- Appointments Agent: Manages scheduling, calendar, and appointment conflicts
- Projects Agent: Tracks painting projects, budgets, crew, and progress
- Proposals Agent: Creates and manages project proposals and estimates
- Contacts Agent: Manages client and supplier contact information
- Reviews Agent: Handles customer reviews, responses, and review requests
- Campaign Agent: Manages marketing campaigns (email/SMS)
- Tasks Agent: Tracks tasks, to-do items, and completion
- Settings Agent: Manages system configuration and business goals

CRITICAL ROUTING RULES:
- Invoice/billing questions → Use the Invoices Agent tool with user_id parameter
- For ANY other domain (projects, appointments, proposals, contacts, reviews, campaigns, tasks, settings):
  → Do NOT call any tool
  → Do NOT make up or hallucinate data
  → Respond with: "I'm sorry, but the [domain] functionality is not yet implemented. Currently, I can only help with invoice-related queries."

When handling invoice queries:
1. Extract the User ID from the system context at the start of the conversation
2. Identify that the query is about invoices/billing
3. Pass the original query AND the user_id to the invoices_agent_tool
4. Return the agent's response without modification

IMPORTANT: Never fabricate information about projects, appointments, contacts, or any other domain. Only use the tools that are actually available to you.

RESPONSE FORMAT:
- Do NOT wrap your response in XML tags like <response>, <answer>, or similar
- Do NOT use any XML-style formatting in your output
"""

# Tools list
SUPERVISOR_TOOLS = [
    invoices_agent_tool,
    # Additional business domain agents will be added in subsequent tasks
]


def get_user_context():
    """
    Get user context from environment variables.
    
    The chat_service sets these environment variables before invoking the supervisor:
    - CURRENT_USER_ID: The authenticated user's ID
    - CURRENT_USER_JWT: The user's JWT token for user-scoped operations
    
    Returns:
        Tuple of (user_id, user_jwt) from environment
    """
    user_id = os.environ.get('CURRENT_USER_ID')
    user_jwt = os.environ.get('CURRENT_USER_JWT')
    return user_id, user_jwt


def create_supervisor_agent(callback_handler=None):
    """
    Create a supervisor agent instance.
    
    Args:
        callback_handler: Optional callback for streaming tokens
        
    Returns:
        Configured Agent instance
    """
    return Agent(
        model=bedrock_model,
        system_prompt=SUPERVISOR_SYSTEM_PROMPT,
        tools=SUPERVISOR_TOOLS,
        callback_handler=callback_handler
    )


# Default agent instance (no streaming)
supervisor_agent = create_supervisor_agent()

if __name__ == "__main__":
    print("Welcome to Supervisor Agent. Type 'exit' to quit or press Ctrl+C.")
    
    # Set a test user ID for direct testing
    test_user_id = os.getenv('SYSTEM_USER_ID', '00000000-0000-0000-0000-000000000000')
    os.environ['CURRENT_USER_ID'] = test_user_id
    print(f"Using test user ID: {test_user_id}")
    
    try:
        while True:
            query = input("Enter your prompt: ")
            if query.lower() == "exit":
                print("Exiting Supervisor Agent. Goodbye!")
                break
            
            # Add user context to the query for the supervisor
            context_query = f"[SYSTEM: User ID is {test_user_id}]\n\n{query}"
            result = supervisor_agent(context_query)
            print("Response:", result)
    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt. Exiting Supervisor Agent. Goodbye!")
