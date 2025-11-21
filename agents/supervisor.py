import os
import logging
from strands import Agent
from strands.models import BedrockModel
import boto3

from dotenv import load_dotenv
load_dotenv() 

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.getLogger('strands').setLevel(logging.INFO)

claude_model = BedrockModel(
    model_id="amazon.nova-lite-v1:0"
)

SUPERVISOR_SYSTEM_PROMPT = """
You are the Supervisor Agent for Canvalo, a painting contractor business management system.
Your role is to analyze user queries and route them to the appropriate specialized agent.

Available agents:
- Invoices Agent: Handles invoice creation, viewing, updating, and payment tracking
- Appointments Agent: Manages scheduling, calendar, and appointment conflicts
- Projects Agent: Tracks painting projects, budgets, crew, and progress
- Proposals Agent: Creates and manages project proposals and estimates
- Contacts Agent: Manages client and supplier contact information
- Reviews Agent: Handles customer reviews, responses, and review requests
- Campaign Agent: Manages marketing campaigns (email/SMS)
- Tasks Agent: Tracks tasks, to-do items, and completion
- Settings Agent: Manages system configuration and business goals

Routing rules:
- Client/customer questions → Contacts Agent
- Project/job questions → Projects Agent
- Scheduling/appointment questions → Appointments Agent
- Proposal/estimate questions → Proposals Agent
- Invoice/billing questions → Invoices Agent
- Review/feedback questions → Reviews Agent
- Marketing/campaign questions → Campaign Agent
- Task/to-do questions → Tasks Agent
- Settings/goals/configuration questions → Settings Agent

When routing:
1. Identify the primary domain from the user's query
2. Pass the original query unchanged to the selected agent
3. Return the agent's response without modification
4. For multi-domain queries, coordinate multiple agents and merge responses
5. For ambiguous queries, ask clarifying questions before routing
"""

supervisor_agent = Agent(
    model=claude_model,
    system_prompt=SUPERVISOR_SYSTEM_PROMPT,
    tools = []  # Business domain agents will be added in subsequent tasks
)

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
