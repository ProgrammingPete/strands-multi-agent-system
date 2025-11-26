import logging
from strands import Agent
from strands.models import BedrockModel

from backend.config import settings

# Import specialized agents
from .invoices_agent import invoices_agent_tool

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.getLogger('strands').setLevel(logging.INFO)

bedrock_model = BedrockModel(
    model_id=settings.bedrock_model_id,
    max_tokens=4096
)

SUPERVISOR_SYSTEM_PROMPT = """
You are the Supervisor Agent for Canvalo, a painting contractor business management system.
Your role is to analyze user queries and route them to the appropriate specialized agent.

IMPLEMENTED AGENTS (you can use these):
- Invoices Agent: Handles invoice creation, viewing, updating, and payment tracking

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
- Invoice/billing questions → Use the Invoices Agent tool
- For ANY other domain (projects, appointments, proposals, contacts, reviews, campaigns, tasks, settings):
  → Do NOT call any tool
  → Do NOT make up or hallucinate data
  → Respond with: "I'm sorry, but the [domain] functionality is not yet implemented. Currently, I can only help with invoice-related queries."

When handling invoice queries:
1. Identify that the query is about invoices/billing
2. Pass the original query unchanged to the invoices_agent_tool
3. Return the agent's response without modification

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
    try:
        while True:
                query = input("Enter your prompt: ")
                if query.lower() == "exit":
                    print("Exiting Supervisor Agent. Goodbye!")
                    break
                result = supervisor_agent(query)
                print("Response:", result)
    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt. Exiting Supervisor Agent. Goodbye!")
