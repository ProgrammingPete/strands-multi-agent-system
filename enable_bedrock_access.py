#!/usr/bin/env python3
"""
Script to check and enable Bedrock model access
"""
import boto3
import os
from dotenv import load_dotenv

load_dotenv()

def check_bedrock_access():
    session = boto3.Session(profile_name=os.getenv("AWS_PROFILE_US_WEST_2"))
    bedrock = session.client('bedrock', region_name='us-west-2')
    
    try:
        # List available models
        response = bedrock.list_foundation_models()
        print("Available models:")
        for model in response['modelSummaries']:
            print(f"- {model['modelId']} ({model['modelName']})")
    except Exception as e:
        print(f"Error: {e}")
        print("\nYou need to enable model access in AWS Bedrock Console:")
        print("1. Go to https://console.aws.amazon.com/bedrock/")
        print("2. Click 'Model access' in the left sidebar")
        print("3. Click 'Request model access'")
        print("4. Enable access for Anthropic Claude models")

if __name__ == "__main__":
    check_bedrock_access()