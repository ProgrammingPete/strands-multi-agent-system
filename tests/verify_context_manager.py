"""
Simple verification script for context manager functionality.
"""
import asyncio
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.context_manager import ContextManager
from backend.models import Message, ChatRequest


async def test_context_manager():
    """Test basic context manager functionality."""
    print("Testing ContextManager...")
    
    # Create context manager
    cm = ContextManager()
    print(f"✓ Created ContextManager with model {cm.model_id}")
    print(f"✓ Token limit: {cm.token_limit}")
    
    # Test 1: Token limit detection with small messages
    print("\nTest 1: Token limit detection (small messages)")
    small_messages = [
        Message(
            id="1",
            content="Short message",
            role="user",
            timestamp=datetime.now()
        )
    ]
    exceeds = cm._exceeds_token_limit(small_messages)
    print(f"  Small messages exceed limit: {exceeds}")
    assert not exceeds, "Small messages should not exceed limit"
    print("  ✓ Passed")
    
    # Test 2: Token limit detection with large messages
    print("\nTest 2: Token limit detection (large messages)")
    # Nova Lite has 300K token limit, so we need ~1.5M characters (with 20% buffer)
    large_content = "x" * 2000000  # 2 million characters
    large_messages = [
        Message(
            id="1",
            content=large_content,
            role="user",
            timestamp=datetime.now()
        )
    ]
    exceeds = cm._exceeds_token_limit(large_messages)
    print(f"  Large messages exceed limit: {exceeds}")
    assert exceeds, "Large messages should exceed limit"
    print("  ✓ Passed")
    
    # Test 3: Context summarization
    print("\nTest 3: Context summarization")
    messages = []
    for i in range(20):
        messages.append(Message(
            id=f"msg_{i}",
            content=f"This is message {i} with some content",
            role="user" if i % 2 == 0 else "assistant",
            timestamp=datetime.now(),
            agent_type="supervisor" if i % 2 == 1 else None
        ))
    
    summarized = await cm._summarize_context(messages)
    print(f"  Original messages: {len(messages)}")
    print(f"  Summarized messages: {len(summarized)}")
    print(f"  Expected: {cm.PRESERVE_RECENT_MESSAGES + 1}")
    assert len(summarized) == cm.PRESERVE_RECENT_MESSAGES + 1, "Should have summary + recent messages"
    assert summarized[0].id == "summary", "First message should be summary"
    assert "Summary of earlier conversation" in summarized[0].content, "Should contain summary text"
    print("  ✓ Passed")
    
    # Test 4: No summarization for small lists
    print("\nTest 4: No summarization for small lists")
    small_list = messages[:5]
    not_summarized = await cm._summarize_context(small_list)
    print(f"  Original: {len(small_list)}, After: {len(not_summarized)}")
    assert len(not_summarized) == len(small_list), "Small lists should not be summarized"
    print("  ✓ Passed")
    
    # Test 5: Message formatting
    print("\nTest 5: Message formatting for LLM")
    test_messages = [
        Message(
            id="1",
            content="Hello",
            role="user",
            timestamp=datetime.now()
        ),
        Message(
            id="2",
            content="Hi there",
            role="assistant",
            timestamp=datetime.now()
        )
    ]
    formatted = cm.format_messages_for_llm(test_messages)
    print(f"  Formatted output:\n{formatted}")
    assert "User: Hello" in formatted, "Should contain user message"
    assert "Assistant: Hi there" in formatted, "Should contain assistant message"
    print("  ✓ Passed")
    
    # Test 6: Token estimation
    print("\nTest 6: Token estimation")
    text = "This is a test message with some content"
    estimated = cm.estimate_token_count(text)
    expected = len(text) // cm.CHARS_PER_TOKEN
    print(f"  Text length: {len(text)}")
    print(f"  Estimated tokens: {estimated}")
    print(f"  Expected: {expected}")
    assert estimated == expected, "Token estimation should match expected"
    print("  ✓ Passed")
    
    print("\n" + "="*50)
    print("All tests passed! ✓")
    print("="*50)


if __name__ == "__main__":
    asyncio.run(test_context_manager())
