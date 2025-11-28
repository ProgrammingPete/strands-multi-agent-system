-- =====================================================
-- PERFORMANCE OPTIMIZATION INDEXES
-- =====================================================
-- Migration: add_performance_indexes
-- Date: 2025-11-28
-- Description: Adds additional indexes for performance optimization
--              as part of Task 23.1 - Optimize database queries
-- Requirements: 21.2
-- =====================================================

-- =====================================================
-- ADDITIONAL INDEXES FOR AGENT_CONVERSATIONS
-- =====================================================

-- Composite index for efficient conversation listing with message count
-- Optimizes: list_conversations query that orders by updated_at
CREATE INDEX IF NOT EXISTS idx_agent_conversations_user_updated_count 
  ON api.agent_conversations(user_id, updated_at DESC, message_count);

-- Index for finding conversations by title (for search functionality)
CREATE INDEX IF NOT EXISTS idx_agent_conversations_title_gin 
  ON api.agent_conversations USING gin(to_tsvector('english', coalesce(title, '')));

-- =====================================================
-- ADDITIONAL INDEXES FOR AGENT_MESSAGES
-- =====================================================

-- Covering index for message loading - includes commonly selected columns
-- This allows index-only scans for the most common query pattern
CREATE INDEX IF NOT EXISTS idx_agent_messages_conversation_covering 
  ON api.agent_messages(conversation_id, created_at ASC) 
  INCLUDE (content, role, agent_type, metadata);

-- Index for recent messages query (used in context building)
-- Optimizes: queries that fetch the N most recent messages
CREATE INDEX IF NOT EXISTS idx_agent_messages_conversation_recent 
  ON api.agent_messages(conversation_id, created_at DESC);

-- Full-text search index on message content (for future search functionality)
CREATE INDEX IF NOT EXISTS idx_agent_messages_content_gin 
  ON api.agent_messages USING gin(to_tsvector('english', content));

-- =====================================================
-- STATISTICS AND ANALYZE
-- =====================================================

-- Update statistics for query planner optimization
ANALYZE api.agent_conversations;
ANALYZE api.agent_messages;

-- =====================================================
-- QUERY OPTIMIZATION NOTES
-- =====================================================
-- 
-- 1. Conversation Listing Query:
--    SELECT * FROM agent_conversations 
--    WHERE user_id = $1 
--    ORDER BY updated_at DESC 
--    LIMIT $2
--    
--    Uses: idx_agent_conversations_user (existing)
--    
-- 2. Message Loading Query:
--    SELECT * FROM agent_messages 
--    WHERE conversation_id = $1 
--    ORDER BY created_at ASC
--    
--    Uses: idx_agent_messages_conversation_covering (new)
--    Benefit: Index-only scan possible with INCLUDE columns
--
-- 3. Recent Messages Query (for context):
--    SELECT * FROM agent_messages 
--    WHERE conversation_id = $1 
--    ORDER BY created_at DESC 
--    LIMIT 10
--    
--    Uses: idx_agent_messages_conversation_recent (new)
--
-- 4. Full-text Search (future):
--    SELECT * FROM agent_messages 
--    WHERE to_tsvector('english', content) @@ to_tsquery('english', $1)
--    
--    Uses: idx_agent_messages_content_gin (new)
-- =====================================================
