import os
import time
from dotenv import load_dotenv
from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import file_read
import boto3
from mcp import StdioServerParameters, stdio_client
from strands.tools.mcp import MCPClient
import logging

load_dotenv()

# Configure logging
logging.getLogger("strands").setLevel(logging.INFO)

# Create a dynamodb table called flights in us-east-1 with string FlightNumber as the partition key. Sleep then check that the table has been successfully created and then use the data from ../project/flights.csv to add items to the table
# check that the table flights has been successfully created in us-east-1  and then use the data from ../project/flights.csv to add

# Create a custom boto3 session
session = boto3.Session(profile_name=os.getenv("AWS_PROFILE"))

print(session.client)

# Create a Bedrock model with the custom session
lite_model = BedrockModel(
    model_id="amazon.nova-lite-v1:0", 
    boto_session=session)

@tool
def sleep() -> str:
    time.sleep(10)
    return "Slept for 10 seconds. Time to re-check status"

#a python function that iserts a row into a dynamodb table
@tool
def insert_dynamodb_item(table_name: str, item: dict) -> str:
    dynamodb = session.client('dynamodb')
    try:
        response = dynamodb.put_item(TableName=table_name, Item=item)
        return f"Item inserted successfully. Response: {response}"
    except Exception as e:
        return f"Error inserting item: {str(e)}"

@tool
def create_dynamodb_table(table_name: str, partition_key: str) -> str:
    """Create a DynamoDB table with a string partition key"""
    dynamodb = session.client('dynamodb')
    try:
        response = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[{'AttributeName': partition_key, 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': partition_key, 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        return f"Table {table_name} creation initiated. Status: {response['TableDescription']['TableStatus']}"
    except Exception as e:
        return f"Error creating table: {str(e)}"

@tool
def check_table_status(table_name: str) -> str:
    """Check the status of a DynamoDB table"""
    dynamodb = session.client('dynamodb')
    try:
        response = dynamodb.describe_table(TableName=table_name)
        return f"Table {table_name} status: {response['Table']['TableStatus']}"
    except Exception as e:
        return f"Error checking table: {str(e)}"


def aws_manager(query: str) -> str:
    aws_prof = os.getenv("AWS_PROFILE")
    #Create a mcp client to connect to the dynamodb server
    # Connect to an MCP server using stdio transport
    stdio_mcp_client = MCPClient(
        lambda: stdio_client(
            StdioServerParameters(
                command="uvx",
                args=["awslabs.aws-api-mcp-server@latest"],
                env={"AWS_PROFILE": str(os.getenv("AWS_PROFILE"))}
            )
        )
    )
    
    with stdio_mcp_client:
        print("Connected to mcp server")
        
        tools = stdio_mcp_client.list_tools_sync() + [file_read, sleep, create_dynamodb_table, check_table_status, insert_dynamodb_item]
        print("tools created")
        aws_manager_agent = Agent(
            model=lite_model,
            tools=tools,
            system_prompt="""You are an AWS operations assistant with access to multiple AWS services.

                When handling requests:
                - For DynamoDB operations: Use the specialized DynamoDB tools
                - For all other AWS services: Use the call_aws tool
                    - For ec2 actions: use the service name "ec2". EC2 instances do not need a key pair. Use AMI ID from launch template.
                    - s3: Bucket and object operations
                    - iam: User and role management
                    - Other AWS services
                - For file operations: Use the file_read tool
                - To sleep: Use the sleep tool

                Example uses:
                - "Create an EC2 instance" → use the call_aws tool
                - "Query DynamoDB table" → use DynamoDB-specific tools
                - "Read configuration file" → use file_read tool
                - "Sleep for 10 seconds" → use sleep tool
                """,
        )
        print("Agent created")
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
