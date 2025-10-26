import os
import readline
from dotenv import load_dotenv
from mcp import StdioServerParameters, stdio_client
from strands import Agent, tool
from strands.tools.mcp import MCPClient
from strands_tools import file_write
from strands.models import BedrockModel
import boto3

load_dotenv()

# Create a custom boto3 session
session = boto3.Session(profile_name=os.getenv("AWS_PROFILE"))

# Create a Bedrock model with the custom session
nova_lite = BedrockModel(model_id="amazon.nova-lite-v1:0", boto_session=session)

# Code here
@tool
def aws_researcher(query: str) -> str:
    
    #create a mcpclient to connect to the aws-documentation-mcp-server
    # Connect to an MCP server using stdio transport
    aws_documentation_mcp_server = MCPClient(
        lambda: stdio_client(
            StdioServerParameters(
                command="uvx",
                args=["awslabs.aws-documentation-mcp-server@latest"]
                # env={"AWS_PROFILE": "AdministratorAccess-038462773691-us-east-1"}
            )
        )
    )
    
    with aws_documentation_mcp_server:
        tools = aws_documentation_mcp_server.list_tools_sync() + [file_write]
        print("Connected to mcp server: aws-documentation-mcp-server")
    
        aws_researcher_agent = Agent(
                model=nova_lite,
                tools=tools,
                system_prompt="""
                    You are a thorough AWS researcher specialized in finding accurate information online. 
                    
                    For each question:
                    1. Determine what information you need
                    2. Search the AWS Documentation for reliable information
                    3. Extract key information and cite your sources
                    4. Store important findings in memory for future reference
                    5. Synthesize what you've found into a clear, comprehensive answer
                    
                    When researching, focus only on AWS documentation. Always provide citations for the information you find. 
                    """,
            )
    
        return str(aws_researcher_agent(query))


if __name__ == "__main__":
    aws_researcher("Why do I need to fill out Model use case details for the anthropic models? How do I complete this")