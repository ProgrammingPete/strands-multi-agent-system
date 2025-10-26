import readline
import time
import os
from mcp import StdioServerParameters, stdio_client
from strands import Agent, tool
from strands.tools.mcp import MCPClient
from strands.models import BedrockModel
from strands_tools import use_aws, file_read
import boto3
from dotenv import load_dotenv

load_dotenv()

# Create a custom boto3 session
print("os.getenv(\"AWS_PROFILE\")", os.getenv("AWS_PROFILE"))
session = boto3.Session(profile_name=os.getenv("AWS_PROFILE"))

# Create a Bedrock model with the custom session
# Try Claude 3 Haiku first (more widely available), fallback to Nova Lite
# try:P
#     lite_model = BedrockModel(model_id="anthropic.claude-3-haiku-20240307-v1:0", boto_session=session)
# except Exception as e:
#     print(f"Claude not available, trying Nova Lite: {e}")
lite_model = BedrockModel(model_id="amazon.nova-lite-v1:0", boto_session=session)

@tool
def sleep() -> str:
    time.sleep(10)
    return "Slept for 10 seconds. Time to re-check status"

@tool
def aws_manager(query: str) -> str:
    # Connect to an MCP server using stdio transport
    stdio_mcp_client = MCPClient(
        lambda: stdio_client(
            StdioServerParameters(
                command="uvx",
                args=["awslabs.dynamodb-mcp-server"],
            )
        )
    )

    # Create an agent with MCP tools
    with stdio_mcp_client:
        # Get the tools from the MCP server
        tools = stdio_mcp_client.list_tools_sync() + [file_read, sleep, use_aws]

        # Create an agent with these tools
        aws_manager_agent = Agent(
            model=lite_model,
            tools=tools,
            system_prompt="""You are an AWS operations assistant with access to multiple AWS services.

When handling requests:
- For DynamoDB operations: Use the specialized DynamoDB tools
- For all other AWS services: Use the use_aws tool
    - For ec2 actions: use the service name "ec2". EC2 instances do not need a key pair. Use AMI ID from launch template.
    - s3: Bucket and object operations
    - iam: User and role management
    - Other AWS services
- For file operations: Use the file_read tool
- To sleep: Use the sleep tool

Example uses:
- "Create an EC2 instance" → use the use_aws tool
- "Query DynamoDB table" → use DynamoDB-specific tools
- "Read configuration file" → use file_read tool
- "Sleep for 10 seconds" → use sleep tool""",
        )
        return str(aws_manager_agent(query))

if __name__ == "__main__":
    print("Welcome to AWS Manager. Type 'exit' to quit or press Ctrl+C.")
    try:
        while True:
            try:
                query = input("Enter your prompt: ")
                if query.lower() == "exit":
                    print("Exiting AWS Manager. Goodbye!")
                    break
                result = aws_manager(query)
                print("Response:", result)
            except Exception as e:
                print(f"An error occurred: {e}")
    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt. Exiting AWS Manager. Goodbye!")
