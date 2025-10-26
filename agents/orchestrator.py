import os
import readline
from dotenv import load_dotenv
from strands import Agent
from strands.models import BedrockModel
import boto3

load_dotenv()
# Add imports from other tools
from coder import coder
from aws_researcher import aws_researcher
from alarm_manager import alarms
from aws_manager import aws_manager

session_us_west_2 = boto3.Session(profile_name=os.getenv("AWS_PROFILE_US_WEST_2"))

claude_model = BedrockModel(
    model_id="anthropic.claude-3-5-haiku-20241022-v1:0", boto_session=session_us_west_2
)

ORCHESTRATOR_SYSTEM_PROMPT = """
You are an assistant that routes queries to specialized agents:
    - When asked to code or read a local file → Use the coder tool
    - When asked to check on AWS account health → Use the alarms tool
    - When asked to perform research on AWS → Use the aws_researcher
    - When asked to perform an action in AWS -> Use aws_manager
    - For simple questions not requiring specialized knowledge → Answer directly

Always select the most appropriate tool based on the user's query.
Do not prompt the user again until a task is complete.
"""

orchestrator_agent = Agent(
    model=claude_model,
    system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
    tools = [coder, alarms, aws_researcher, aws_manager]
)

if __name__ == "__main__":
    print("Welcome to AWS orchestrator_agent. Type 'exit' to quit or press Ctrl+C.")
    try:
        while True:
                query = input("Enter your prompt: ")
                if query.lower() == "exit":
                    print("Exiting orchestrator_agent. Goodbye!")
                    break
                result = orchestrator_agent(query)
                print("Response:", result)
    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt. Exiting orchestrator_agent. Goodbye!")