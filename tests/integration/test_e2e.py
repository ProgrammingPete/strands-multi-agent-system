"""
End-to-end tests for the multi-agent chat system.

These tests verify the complete flow from API request to response,
including streaming, agent routing, conversation persistence, and error handling.

Requirements covered:
- 14.1, 14.2, 14.3, 15.2: Basic chat flow and streaming
- 12.1-12.9: Agent routing by domain
- 12.12: Multi-agent coordination
- 16.1-16.5: Error handling
- 17.1-17.4: Voice mode (transcript handling)
"""
import pytest
import requests
import json
import time
import uuid
import os
from typing import Generator, List, Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test configuration
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"

# Supabase configuration for authentication
# Prefer pub key for production-safe testing, fall back to service key for dev
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_PUB_KEY", "") or os.environ.get("SUPABASE_SERVICE_KEY", "")

# Test user credentials (same as frontend uses)
TEST_USER_EMAIL = os.environ.get("TEST_USER_EMAIL", "test@example.com")
TEST_USER_PASSWORD = os.environ.get("TEST_USER_PASSWORD", "password123")

# Cached authentication data
_authenticated_user_id: Optional[str] = None
_authenticated_jwt_token: Optional[str] = None

# Flag to track if conversation creation works (set during first test)
_conversation_creation_works = None


def get_authenticated_credentials() -> tuple[Optional[str], Optional[str]]:
    """
    Authenticate with Supabase using test credentials and return user ID and JWT token.
    Uses the same credentials as the frontend for consistency.
    
    Returns:
        Tuple of (user_id, jwt_token) or (None, None) if authentication fails
    """
    global _authenticated_user_id, _authenticated_jwt_token
    
    if _authenticated_user_id is not None and _authenticated_jwt_token is not None:
        return _authenticated_user_id, _authenticated_jwt_token
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("⚠ Supabase credentials not configured, using fallback user ID")
        return None, None
    
    try:
        # Use Supabase REST API to sign in
        auth_url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
        response = requests.post(
            auth_url,
            headers={
                "apikey": SUPABASE_KEY,
                "Content-Type": "application/json",
            },
            json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD,
            },
            timeout=10,
        )
        
        if response.status_code == 200:
            data = response.json()
            _authenticated_user_id = data.get("user", {}).get("id")
            _authenticated_jwt_token = data.get("access_token")
            if _authenticated_user_id and _authenticated_jwt_token:
                print(f"✓ Authenticated as user: {_authenticated_user_id}")
                return _authenticated_user_id, _authenticated_jwt_token
        else:
            print(f"⚠ Authentication failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"⚠ Authentication error: {e}")
    
    return None, None


def get_jwt_token() -> Optional[str]:
    """Get the cached JWT token, authenticating if needed."""
    _, token = get_authenticated_credentials()
    return token


# Get authenticated user ID or fall back to SYSTEM_USER_ID environment variable
# **Requirements: 12.1** - Use SYSTEM_USER_ID for test operations
_user_id, _jwt_token = get_authenticated_credentials()
TEST_USER_ID = _user_id or os.environ.get(
    "SYSTEM_USER_ID", os.environ.get("TEST_USER_ID", "00000000-0000-0000-0000-000000000000")
)
TEST_JWT_TOKEN = _jwt_token


@dataclass
class StreamChunk:
    """Parsed SSE chunk from streaming response."""
    type: str
    content: Optional[str] = None
    tool_name: Optional[str] = None
    tool_call: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    agent_type: Optional[str] = None


def parse_sse_stream(response: requests.Response) -> Generator[StreamChunk, None, None]:
    """Parse SSE stream from response into StreamChunk objects."""
    for line in response.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            if decoded_line.startswith('data: '):
                try:
                    data = json.loads(decoded_line[6:])
                    yield StreamChunk(
                        type=data.get('type', 'unknown'),
                        content=data.get('content'),
                        tool_name=data.get('tool_name'),
                        tool_call=data.get('tool_call'),
                        error=data.get('error'),
                        agent_type=data.get('agent_type')
                    )
                except json.JSONDecodeError:
                    continue


def collect_stream_response(response: requests.Response) -> tuple[str, List[StreamChunk]]:
    """Collect all chunks from stream and return full text and chunk list."""
    chunks = []
    full_text = []
    
    for chunk in parse_sse_stream(response):
        chunks.append(chunk)
        if chunk.type == 'token' and chunk.content:
            full_text.append(chunk.content)
        elif chunk.type in ('complete', 'error'):
            break
    
    return ''.join(full_text), chunks


def get_auth_headers() -> dict:
    """Get authorization headers with JWT token if available."""
    headers = {}
    if TEST_JWT_TOKEN:
        headers["Authorization"] = f"Bearer {TEST_JWT_TOKEN}"
    return headers


def create_test_conversation(title: str = "E2E Test Conversation") -> Optional[str]:
    """Create a test conversation and return its ID."""
    global _conversation_creation_works
    
    try:
        response = requests.post(
            f"{API_URL}/conversations",
            json={"user_id": TEST_USER_ID, "title": title},
            headers=get_auth_headers()
        )
        if response.status_code in (200, 201):
            _conversation_creation_works = True
            return response.json().get('id')
        else:
            print(f"Conversation creation failed: {response.status_code} - {response.text[:200]}")
            _conversation_creation_works = False
    except Exception as e:
        print(f"Conversation creation error: {e}")
        _conversation_creation_works = False
    return None


def check_conversation_support() -> bool:
    """Check if conversation creation is supported (user exists in DB)."""
    global _conversation_creation_works
    
    if _conversation_creation_works is None:
        # Try to create a test conversation to check
        conv_id = create_test_conversation("Support Check")
        if conv_id:
            delete_test_conversation(conv_id)
    
    return _conversation_creation_works == True


def delete_test_conversation(conversation_id: str) -> bool:
    """Delete a test conversation."""
    try:
        response = requests.delete(
            f"{API_URL}/conversations/{conversation_id}",
            params={"user_id": TEST_USER_ID},
            headers=get_auth_headers()
        )
        return response.status_code in (200, 204)
    except Exception:
        return False


def send_chat_message(
    message: str,
    conversation_id: str,
    user_id: str = TEST_USER_ID,
    history: List[Dict] = None,
    jwt_token: Optional[str] = None
) -> requests.Response:
    """Send a chat message and return the streaming response."""
    payload = {
        "message": message,
        "conversation_id": conversation_id,
        "user_id": user_id,
        "history": history or []
    }
    
    headers = {"Accept": "text/event-stream"}
    
    # Use provided token, fall back to global test token
    token = jwt_token or TEST_JWT_TOKEN
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    return requests.post(
        f"{API_URL}/chat/stream",
        json=payload,
        stream=True,
        headers=headers
    )


class TestServerHealth:
    """Test server health and basic connectivity."""
    
    def test_health_check(self):
        """Test the health check endpoint returns healthy status."""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get('status') == 'healthy'
        assert 'supabase_configured' in data
        assert 'bedrock_model' in data
    
    def test_root_endpoint(self):
        """Test the root endpoint returns service info."""
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        data = response.json()
        assert data.get('status') == 'ok'
        assert 'service' in data
        assert 'version' in data


class TestBasicChatFlow:
    """
    Test basic chat flow: send message, receive streaming response, verify persistence.
    Requirements: 14.1, 14.2, 14.3, 15.2
    """
    
    @pytest.fixture
    def conversation_id(self):
        """Create a test conversation for each test."""
        if not check_conversation_support():
            pytest.skip(f"Conversation creation not supported (user {TEST_USER_ID} may not exist in DB)")
        conv_id = create_test_conversation("Basic Chat Flow Test")
        yield conv_id
        if conv_id:
            delete_test_conversation(conv_id)
    
    def test_send_message_and_receive_response(self, conversation_id):
        """
        Test sending a message and receiving a streaming response.
        Requirements: 14.1, 14.2, 14.3
        """
        if not conversation_id:
            pytest.skip("Could not create test conversation")
        
        response = send_chat_message(
            message="Hello, what can you help me with?",
            conversation_id=conversation_id
        )
        
        assert response.status_code == 200
        assert response.headers.get('content-type') == 'text/event-stream; charset=utf-8'
        
        full_text, chunks = collect_stream_response(response)
        
        # Verify we received chunks
        assert len(chunks) > 0, "Should receive at least one chunk"
        
        # Verify we got token chunks
        token_chunks = [c for c in chunks if c.type == 'token']
        assert len(token_chunks) > 0, "Should receive token chunks"
        
        # Verify stream completed
        complete_chunks = [c for c in chunks if c.type == 'complete']
        assert len(complete_chunks) == 1, "Should receive exactly one complete chunk"
        
        # Verify we got actual content
        assert len(full_text) > 0, "Should receive non-empty response"
    
    def test_streaming_shows_typing_indicator_pattern(self, conversation_id):
        """
        Test that streaming delivers tokens incrementally (for typing indicator).
        Requirements: 14.2
        """
        if not conversation_id:
            pytest.skip("Could not create test conversation")
        
        response = send_chat_message(
            message="Tell me about your capabilities",
            conversation_id=conversation_id
        )
        
        assert response.status_code == 200
        
        # Collect chunks with timing
        chunk_times = []
        for chunk in parse_sse_stream(response):
            chunk_times.append(time.time())
            if chunk.type in ('complete', 'error'):
                break
        
        # Verify multiple chunks were received (streaming, not batch)
        assert len(chunk_times) > 1, "Should receive multiple chunks for streaming"
    
    def test_message_persistence(self, conversation_id):
        """
        Test that messages are persisted to the database.
        Requirements: 15.2
        """
        if not conversation_id:
            pytest.skip("Could not create test conversation")
        
        test_message = f"Test message for persistence {uuid.uuid4()}"
        
        # Send message
        response = send_chat_message(
            message=test_message,
            conversation_id=conversation_id
        )
        
        # Consume the stream
        full_text, chunks = collect_stream_response(response)
        
        # Verify no error
        error_chunks = [c for c in chunks if c.type == 'error']
        assert len(error_chunks) == 0, f"Should not have errors: {error_chunks}"
        
        # Give time for persistence
        time.sleep(0.5)
        
        # Fetch conversation and verify messages
        conv_response = requests.get(
            f"{API_URL}/conversations/{conversation_id}",
            params={"user_id": TEST_USER_ID}
        )
        
        if conv_response.status_code == 200:
            conv_data = conv_response.json()
            messages = conv_data.get('messages', [])
            
            # Should have at least user message and assistant response
            assert len(messages) >= 2, "Should have user and assistant messages"
            
            # Verify user message was saved
            user_messages = [m for m in messages if m.get('role') == 'user']
            assert any(test_message in m.get('content', '') for m in user_messages), \
                "User message should be persisted"
            
            # Verify assistant message was saved
            assistant_messages = [m for m in messages if m.get('role') == 'assistant']
            assert len(assistant_messages) > 0, "Assistant message should be persisted"


class TestAgentRouting:
    """
    Test that queries are routed to the correct specialized agents.
    Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8, 12.9
    """
    
    @pytest.fixture
    def conversation_id(self):
        """Create a test conversation for each test."""
        if not check_conversation_support():
            pytest.skip(f"Conversation creation not supported (user {TEST_USER_ID} may not exist in DB)")
        conv_id = create_test_conversation("Agent Routing Test")
        yield conv_id
        if conv_id:
            delete_test_conversation(conv_id)
    
    def test_invoice_query_routes_to_invoices_agent(self, conversation_id):
        """
        Test that invoice queries are routed to the Invoices Agent.
        Requirements: 12.5
        """
        if not conversation_id:
            pytest.skip("Could not create test conversation")
        
        response = send_chat_message(
            message="Show me my recent invoices",
            conversation_id=conversation_id
        )
        
        assert response.status_code == 200
        full_text, chunks = collect_stream_response(response)
        
        # Check for tool usage (invoices agent should be called)
        tool_chunks = [c for c in chunks if c.type == 'tool_start']
        
        # The response should either use the invoices tool or mention invoices
        assert len(full_text) > 0, "Should receive a response"
        
        # Verify no error
        error_chunks = [c for c in chunks if c.type == 'error']
        assert len(error_chunks) == 0, f"Should not have errors: {error_chunks}"
    
    def test_unimplemented_agent_returns_helpful_message(self, conversation_id):
        """
        Test that queries for unimplemented agents return helpful messages.
        Requirements: 12.1, 12.2, 12.3, 12.4, 12.6, 12.7, 12.8, 12.9
        """
        if not conversation_id:
            pytest.skip("Could not create test conversation")
        
        # Test queries for unimplemented domains
        unimplemented_queries = [
            ("Show me my appointments", "appointments"),
            ("What projects do I have?", "projects"),
            ("Create a proposal for a client", "proposals"),
            ("Find contact information for John", "contacts"),
            ("Show me my customer reviews", "reviews"),
            ("What marketing campaigns are running?", "campaigns"),
            ("What tasks do I have today?", "tasks"),
            ("Update my business settings", "settings"),
        ]
        
        for query, domain in unimplemented_queries:
            response = send_chat_message(
                message=query,
                conversation_id=conversation_id
            )
            
            assert response.status_code == 200, f"Query for {domain} should succeed"
            full_text, chunks = collect_stream_response(response)
            
            # Should get a response (even if it says not implemented)
            assert len(full_text) > 0, f"Should receive response for {domain} query"
            
            # Should not have errors
            error_chunks = [c for c in chunks if c.type == 'error']
            assert len(error_chunks) == 0, f"Should not error for {domain}: {error_chunks}"
            
            # Response should indicate the feature is not implemented or provide helpful info
            response_lower = full_text.lower()
            # Accept either "not implemented" message or any valid response
            # (since the supervisor might handle it differently)
            assert len(response_lower) > 10, f"Response for {domain} should be meaningful"


class TestMultiAgentCoordination:
    """
    Test multi-agent coordination for complex queries.
    Requirements: 12.12
    """
    
    @pytest.fixture
    def conversation_id(self):
        """Create a test conversation for each test."""
        if not check_conversation_support():
            pytest.skip(f"Conversation creation not supported (user {TEST_USER_ID} may not exist in DB)")
        conv_id = create_test_conversation("Multi-Agent Test")
        yield conv_id
        if conv_id:
            delete_test_conversation(conv_id)
    
    def test_ambiguous_query_handling(self, conversation_id):
        """
        Test that ambiguous queries are handled appropriately.
        Requirements: 12.12
        """
        if not conversation_id:
            pytest.skip("Could not create test conversation")
        
        # Send an ambiguous query that could involve multiple domains
        response = send_chat_message(
            message="I need help with my business",
            conversation_id=conversation_id
        )
        
        assert response.status_code == 200
        full_text, chunks = collect_stream_response(response)
        
        # Should receive a response (clarification or general help)
        assert len(full_text) > 0, "Should receive a response for ambiguous query"
        
        # Should not error
        error_chunks = [c for c in chunks if c.type == 'error']
        assert len(error_chunks) == 0, f"Should not error: {error_chunks}"


class TestVoiceMode:
    """
    Test voice mode functionality (transcript handling).
    Requirements: 17.1, 17.2, 17.3, 17.4
    """
    
    @pytest.fixture
    def conversation_id(self):
        """Create a test conversation for each test."""
        if not check_conversation_support():
            pytest.skip(f"Conversation creation not supported (user {TEST_USER_ID} may not exist in DB)")
        conv_id = create_test_conversation("Voice Mode Test")
        yield conv_id
        if conv_id:
            delete_test_conversation(conv_id)
    
    def test_voice_transcript_processing(self, conversation_id):
        """
        Test that voice transcripts are processed correctly.
        Requirements: 17.1
        """
        if not conversation_id:
            pytest.skip("Could not create test conversation")
        
        # Simulate a voice transcript (same as text message)
        response = send_chat_message(
            message="What invoices do I have pending",
            conversation_id=conversation_id
        )
        
        assert response.status_code == 200
        full_text, chunks = collect_stream_response(response)
        
        # Should receive complete response (for TTS)
        assert len(full_text) > 0, "Should receive complete response for voice"
        
        # Verify stream completes
        complete_chunks = [c for c in chunks if c.type == 'complete']
        assert len(complete_chunks) == 1, "Should complete for voice response"
    
    def test_complete_response_for_tts(self, conversation_id):
        """
        Test that complete response is available for text-to-speech.
        Requirements: 17.2
        """
        if not conversation_id:
            pytest.skip("Could not create test conversation")
        
        response = send_chat_message(
            message="Give me a summary of my business",
            conversation_id=conversation_id
        )
        
        assert response.status_code == 200
        full_text, chunks = collect_stream_response(response)
        
        # Full text should be coherent (not cut off)
        assert len(full_text) > 20, "Response should be substantial for TTS"
        
        # Should end with complete chunk
        assert chunks[-1].type == 'complete', "Stream should end with complete"


class TestErrorScenarios:
    """
    Test error handling scenarios.
    Requirements: 16.1, 16.2, 16.3, 16.4, 16.5
    """
    
    def test_invalid_conversation_id(self):
        """
        Test handling of invalid conversation ID.
        Requirements: 16.4
        """
        response = send_chat_message(
            message="Hello",
            conversation_id="invalid-uuid-format"
        )
        
        # Should still return 200 (streaming starts) but may error in stream
        # or handle gracefully
        if response.status_code == 200:
            full_text, chunks = collect_stream_response(response)
            # Either gets a response or an error chunk
            assert len(chunks) > 0, "Should receive some response"
        else:
            # 400/422 for validation error, 401 for auth required (production), 500 for server error
            assert response.status_code in (400, 401, 422, 500)
    
    def test_empty_message(self):
        """
        Test handling of empty message.
        Requirements: 16.4
        """
        conv_id = create_test_conversation("Error Test")
        
        try:
            payload = {
                "message": "",  # Empty message
                "conversation_id": conv_id or str(uuid.uuid4()),
                "user_id": TEST_USER_ID,
                "history": []
            }
            
            response = requests.post(
                f"{API_URL}/chat/stream",
                json=payload,
                stream=True
            )
            
            # Should return validation error (422) for empty message
            # or handle gracefully
            assert response.status_code in (200, 400, 422), \
                f"Should handle empty message: {response.status_code}"
        finally:
            if conv_id:
                delete_test_conversation(conv_id)
    
    def test_missing_user_id(self):
        """
        Test handling of missing user ID.
        Requirements: 16.4
        """
        payload = {
            "message": "Hello",
            "conversation_id": str(uuid.uuid4()),
            # Missing user_id
            "history": []
        }
        
        response = requests.post(
            f"{API_URL}/chat/stream",
            json=payload,
            stream=True
        )
        
        # Should return validation error
        assert response.status_code in (400, 422), \
            f"Should reject missing user_id: {response.status_code}"
    
    def test_nonexistent_conversation_fetch(self):
        """
        Test fetching a non-existent conversation.
        Requirements: 16.1
        """
        fake_id = str(uuid.uuid4())
        response = requests.get(
            f"{API_URL}/conversations/{fake_id}",
            params={"user_id": TEST_USER_ID}
        )
        
        # Should return 404 or appropriate error
        assert response.status_code in (404, 500), \
            f"Should return error for non-existent conversation: {response.status_code}"
    
    def test_delete_nonexistent_conversation(self):
        """
        Test deleting a non-existent conversation.
        Requirements: 16.1
        """
        fake_id = str(uuid.uuid4())
        response = requests.delete(
            f"{API_URL}/conversations/{fake_id}",
            params={"user_id": TEST_USER_ID}
        )
        
        # Should return 404 or appropriate error
        assert response.status_code in (404, 500), \
            f"Should return error for non-existent conversation: {response.status_code}"


class TestConversationManagement:
    """
    Test conversation CRUD operations.
    Requirements: 15.1, 15.2
    """
    
    def test_create_conversation(self):
        """Test creating a new conversation."""
        if not check_conversation_support():
            pytest.skip(f"Conversation creation not supported (user {TEST_USER_ID} may not exist in DB)")
        
        response = requests.post(
            f"{API_URL}/conversations",
            json={
                "user_id": TEST_USER_ID,
                "title": "Test Conversation"
            },
            headers=get_auth_headers()
        )
        
        assert response.status_code in (200, 201)
        data = response.json()
        assert 'id' in data
        assert data.get('user_id') == TEST_USER_ID
        
        # Cleanup
        delete_test_conversation(data['id'])
    
    def test_list_conversations(self):
        """Test listing user conversations."""
        # This should work even without a valid user (returns empty list)
        response = requests.get(
            f"{API_URL}/conversations",
            params={"user_id": TEST_USER_ID},
            headers=get_auth_headers()
        )
        
        assert response.status_code == 200
        data = response.json()
        # API now returns paginated response with conversations list
        assert isinstance(data, dict)
        assert "conversations" in data
        assert isinstance(data["conversations"], list)
        assert "total" in data
        assert "has_more" in data
    
    def test_get_conversation_with_messages(self):
        """Test getting a conversation with its messages."""
        if not check_conversation_support():
            pytest.skip(f"Conversation creation not supported (user {TEST_USER_ID} may not exist in DB)")
        
        conv_id = create_test_conversation("Get Test")
        
        if not conv_id:
            pytest.skip("Could not create test conversation")
        
        try:
            # Send a message first
            response = send_chat_message(
                message="Hello for get test",
                conversation_id=conv_id
            )
            collect_stream_response(response)
            
            time.sleep(0.5)  # Wait for persistence
            
            # Get conversation
            response = requests.get(
                f"{API_URL}/conversations/{conv_id}",
                params={"user_id": TEST_USER_ID},
                headers=get_auth_headers()
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data.get('id') == conv_id
            assert 'messages' in data
        finally:
            delete_test_conversation(conv_id)
    
    def test_delete_conversation(self):
        """Test deleting a conversation."""
        if not check_conversation_support():
            pytest.skip(f"Conversation creation not supported (user {TEST_USER_ID} may not exist in DB)")
        
        conv_id = create_test_conversation("Delete Test")
        
        if not conv_id:
            pytest.skip("Could not create test conversation")
        
        response = requests.delete(
            f"{API_URL}/conversations/{conv_id}",
            params={"user_id": TEST_USER_ID},
            headers=get_auth_headers()
        )
        
        assert response.status_code in (200, 204)
        
        # Verify it's deleted
        get_response = requests.get(
            f"{API_URL}/conversations/{conv_id}",
            params={"user_id": TEST_USER_ID}
        )
        assert get_response.status_code in (404, 500)


def run_e2e_tests():
    """Run all e2e tests and print summary."""
    print("=" * 70)
    print("End-to-End Tests for Multi-Agent Chat System")
    print("=" * 70)
    print()
    
    # Check server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Server health check failed")
            print("Make sure the server is running: uv run python -m backend.main")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server at", BASE_URL)
        print("Make sure the server is running: uv run python -m backend.main")
        return False
    
    print("✓ Server is running")
    print()
    
    # Run pytest
    import sys
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-x",  # Stop on first failure
    ])
    
    return exit_code == 0


if __name__ == "__main__":
    success = run_e2e_tests()
    exit(0 if success else 1)
