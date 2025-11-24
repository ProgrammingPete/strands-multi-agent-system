"""
Tests for context management functionality.
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.context_manager import ContextManager
from backend.models import Message, ChatRequest


class TestContextManager:
    """Test suite for ContextManager."""
    
    @pytest.fixture
    def context_manager(self):
        """Create a context manager instance for testing."""
        with patch('backend.context_manager.ConversationService'):
            return ContextManager()
    
    @pytest.fixture
    def sample_messages(self):
        """Create sample messages for testing."""
        messages = []
        for i in range(20):
            messages.append(Message(
                id=f"msg_{i}",
                content=f"This is message {i} with some content",
                role="user" if i % 2 == 0 else "assistant",
                timestamp=datetime.now(),
                agent_type="supervisor" if i % 2 == 1 else None
            ))
        return messages
    
    def test_exceeds_token_limit_false(self, context_manager):
        """Test that small message history doesn't exceed token limit."""
        messages = [
            Message(
                id="1",
                content="Short message",
                role="user",
                timestamp=datetime.now()
            )
        ]
        
        assert not context_manager._exceeds_token_limit(messages)
    
    def test_exceeds_token_limit_true(self, context_manager):
        """Test that large message history exceeds token limit."""
        # Create a very large message that definitely exceeds the token limit
        # Token limit is 300,000 for nova-lite
        # With 4 chars per token and 20% buffer: need > 300,000 / 1.2 * 4 = 1,000,000 chars
        # Use 1.5 million to be safe
        large_content = "x" * 1500000  # 1.5 million characters
        messages = [
            Message(
                id="1",
                content=large_content,
                role="user",
                timestamp=datetime.now()
            )
        ]
        
        assert context_manager._exceeds_token_limit(messages)
    
    @pytest.mark.asyncio
    async def test_summarize_context_preserves_recent(self, context_manager, sample_messages):
        """Test that summarization preserves recent messages."""
        summarized = await context_manager._summarize_context(sample_messages)
        
        # Should have summary + recent messages
        assert len(summarized) == context_manager.PRESERVE_RECENT_MESSAGES + 1
        
        # Last N messages should be unchanged
        for i in range(context_manager.PRESERVE_RECENT_MESSAGES):
            original_idx = len(sample_messages) - context_manager.PRESERVE_RECENT_MESSAGES + i
            assert summarized[i + 1].id == sample_messages[original_idx].id
            assert summarized[i + 1].content == sample_messages[original_idx].content
    
    @pytest.mark.asyncio
    async def test_summarize_context_creates_summary(self, context_manager, sample_messages):
        """Test that summarization creates a summary message."""
        summarized = await context_manager._summarize_context(sample_messages)
        
        # First message should be the summary
        assert summarized[0].id == "summary"
        assert "Summary of earlier conversation" in summarized[0].content
        assert summarized[0].metadata.get("is_summary") is True
    
    @pytest.mark.asyncio
    async def test_summarize_context_no_summarization_needed(self, context_manager):
        """Test that small message lists are not summarized."""
        messages = [
            Message(
                id=f"msg_{i}",
                content=f"Message {i}",
                role="user",
                timestamp=datetime.now()
            )
            for i in range(5)
        ]
        
        summarized = await context_manager._summarize_context(messages)
        
        # Should return original messages unchanged
        assert len(summarized) == len(messages)
        assert summarized == messages
    
    def test_format_messages_for_llm(self, context_manager):
        """Test message formatting for LLM context."""
        messages = [
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
        
        formatted = context_manager.format_messages_for_llm(messages)
        
        assert "User: Hello" in formatted
        assert "Assistant: Hi there" in formatted
    
    def test_estimate_token_count(self, context_manager):
        """Test token count estimation."""
        text = "This is a test message"
        estimated = context_manager.estimate_token_count(text)
        
        # Should be roughly len(text) / CHARS_PER_TOKEN
        expected = len(text) // context_manager.CHARS_PER_TOKEN
        assert estimated == expected
    
    @pytest.mark.asyncio
    async def test_build_context_empty_history(self, context_manager):
        """Test building context with empty history."""
        request = ChatRequest(
            message="Test message",
            conversation_id="conv_1",
            user_id="user_1",
            history=[]
        )
        
        with patch.object(context_manager, '_load_conversation_history', return_value=[]):
            context = await context_manager.build_context(request, include_user_profile=False)
            
            # Should return empty string for empty history
            assert context == ""
    
    @pytest.mark.asyncio
    async def test_build_context_with_history(self, context_manager):
        """Test building context with message history."""
        messages = [
            Message(
                id="1",
                content="Previous message",
                role="user",
                timestamp=datetime.now()
            )
        ]
        
        request = ChatRequest(
            message="Test message",
            conversation_id="conv_1",
            user_id="user_1",
            history=messages
        )
        
        context = await context_manager.build_context(request, include_user_profile=False)
        
        assert "Previous conversation:" in context
        assert "User: Previous message" in context
    
    @pytest.mark.asyncio
    async def test_build_context_with_user_profile(self, context_manager):
        """Test building context with user profile."""
        request = ChatRequest(
            message="Test message",
            conversation_id="conv_1",
            user_id="user_1",
            history=[]
        )
        
        with patch.object(context_manager, '_load_conversation_history', return_value=[]):
            context = await context_manager.build_context(request, include_user_profile=True)
            
            # Should include user profile
            assert "User ID: user_1" in context
            assert "Business Type: Painting Contractor" in context


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
