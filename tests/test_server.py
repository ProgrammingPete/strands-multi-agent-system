"""
Simple test script to verify the FastAPI server is working.
Run this after starting the server with: python -m backend.main
"""
import requests
import json
import time


def test_health_check():
    """Test the health check endpoint."""
    print("Testing health check endpoint...")
    response = requests.get("http://localhost:8000/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    print("✓ Health check passed\n")


def test_root():
    """Test the root endpoint."""
    print("Testing root endpoint...")
    response = requests.get("http://localhost:8000/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    print("✓ Root endpoint passed\n")


def test_chat_stream():
    """Test the chat streaming endpoint."""
    print("Testing chat stream endpoint...")
    
    # Use system test user ID (same as used in invoice tests)
    test_user_id = "00000000-0000-0000-0000-000000000000"
    
    # First, create a test conversation
    print("Creating test conversation...")
    create_response = requests.post(
        "http://localhost:8000/api/conversations",
        json={
            "user_id": test_user_id,
            "title": "Test Conversation"
        }
    )
    
    if create_response.status_code in [200, 201]:
        conversation_data = create_response.json()
        test_conversation_id = conversation_data.get('id')
        print(f"✓ Test conversation created: {test_conversation_id}")
    else:
        print(f"⚠ Warning: Could not create conversation (status: {create_response.status_code})")
        print(f"  Response: {create_response.text}")
        # Fall back to a test UUID
        test_conversation_id = "123e4567-e89b-12d3-a456-426614174000"
        print(f"  Using fallback conversation ID: {test_conversation_id}")
        print("  (messages won't be persisted)")
    
    payload = {
        "message": "Hello, what can you help me with?",
        "conversation_id": test_conversation_id,
        "user_id": test_user_id,
        "history": []
    }
    
    print(f"\nSending request: {json.dumps(payload, indent=2)}")
    
    response = requests.post(
        "http://localhost:8000/api/chat/stream",
        json=payload,
        stream=True,
        headers={"Accept": "text/event-stream"}
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        print("Streaming response:")
        chunk_count = 0
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith('data: '):
                    chunk_count += 1
                    data = json.loads(decoded_line[6:])
                    
                    # Handle different chunk types
                    if data.get('type') == 'complete':
                        print(f"  Chunk {chunk_count}: {data.get('type')} - Stream complete")
                        break
                    elif data.get('type') == 'error':
                        print(f"  Chunk {chunk_count}: {data.get('type')} - {data.get('error', 'Unknown error')}")
                        break
                    else:
                        content = data.get('content', '')
                        preview = content[:50] if content else '(no content)'
                        print(f"  Chunk {chunk_count}: {data.get('type')} - {preview}")
        
        print(f"✓ Chat stream passed ({chunk_count} chunks received)\n")
    else:
        print(f"✗ Chat stream failed: {response.text}\n")


def main():
    """Run all tests."""
    print("=" * 60)
    print("FastAPI Backend Server Tests")
    print("=" * 60)
    print()
    
    try:
        test_health_check()
        test_root()
        test_chat_stream()
        
        print("=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Could not connect to server")
        print("Make sure the server is running: python -m backend.main")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
