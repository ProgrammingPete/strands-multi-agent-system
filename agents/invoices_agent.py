"""
Invoices Agent - Specialized agent for invoice management.

This agent handles invoice creation, viewing, updating, and payment tracking
for the Canvalo painting contractor business management system.
"""

import logging
from strands import Agent, tool
from strands.models import BedrockModel
from dotenv import load_dotenv

# Import invoice-specific tools
from .invoice_tools import get_invoices, create_invoice, update_invoice, delete_invoice

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# System prompt for the Invoices Agent
INVOICES_AGENT_SYSTEM_PROMPT = """
You are the Invoices Agent for Canvalo, a painting contractor business management system.
You are an expert in invoice management, billing, and payment tracking.

Your responsibilities:
- Create new invoices with client information, line items, dates, and payment terms
- View and retrieve invoice information from the database
- Update existing invoices (status, payment information, line items)
- Track invoice payments and payment status
- Format invoice data in a clear, professional manner
- Help users understand invoice status and payment history

When creating invoices:
1. Collect all required information: client, items/services, amounts, dates
2. Ensure all line items have descriptions and amounts
3. Calculate totals correctly
4. Set appropriate due dates and payment terms

When displaying invoices:
1. Format currency values clearly (e.g., $1,234.56)
2. Show dates in a readable format
3. Display line items with descriptions and amounts
4. Show payment status prominently (draft, sent, paid, overdue)
5. Include client information

When updating invoices:
1. Verify the invoice exists before updating
2. Validate any changes to amounts or dates
3. Update payment status when payments are received
4. Maintain audit trail of changes

Always be professional, accurate, and helpful. If information is missing or unclear,
ask clarifying questions before proceeding.
"""

# Initialize the Bedrock model
bedrock_model = BedrockModel(
    model_id="amazon.nova-lite-v1:0"
)


@tool
def invoices_agent_tool(query: str) -> str:
    """
    Invoice management agent that handles invoice creation, viewing, updating, and payment tracking.
    
    This agent is an expert in invoicing and can help with:
    - Creating new invoices with line items and payment terms
    - Viewing invoice details and status
    - Updating invoice information and payment status
    - Tracking payments and overdue invoices
    - Formatting invoice data for display
    
    Args:
        query: The user's query about invoices
    
    Returns:
        Response from the invoices agent
    """
    try:
        # Create agent with invoice management tools
        agent = Agent(
            model=bedrock_model,
            system_prompt=INVOICES_AGENT_SYSTEM_PROMPT,
            tools=[
                get_invoices,
                create_invoice,
                update_invoice,
                delete_invoice
            ]
        )
        
        logger.info(f"Invoices agent processing query: {query}")
        response = agent(query)
        logger.info("Invoices agent completed successfully")
        
        return str(response)
        
    except Exception as e:
        error_msg = f"Error in invoices_agent: {str(e)}"
        logger.error(error_msg)
        return f"I apologize, but I encountered an error while processing your invoice request. Please try again or contact support if the issue persists. Error: {str(e)}"


if __name__ == "__main__":
    """Test the invoices agent directly."""
    print("Invoices Agent Test Mode")
    print("=" * 50)
    print("Type 'exit' to quit\n")
    
    try:
        while True:
            query = input("Enter your invoice query: ")
            if query.lower() == "exit":
                print("Exiting Invoices Agent. Goodbye!")
                break
            
            response = invoices_agent_tool(query)
            print(f"\nResponse: {response}\n")
            print("-" * 50)
            
    except KeyboardInterrupt:
        print("\n\nReceived keyboard interrupt. Exiting Invoices Agent. Goodbye!")
