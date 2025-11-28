# Performance Optimization Guide

This document describes the performance optimizations implemented in Task 23 of the multi-agent chat system.

## Overview

Performance optimizations focus on two main areas:
1. **Database Query Optimization** (Task 23.1)
2. **Streaming Latency Optimization** (Task 23.2)

---

## Database Query Optimization (Task 23.1)

### New Indexes

The following indexes have been added to improve query performance:

```sql
-- Composite index for conversation listing with message count
CREATE INDEX idx_agent_conversations_user_updated_count 
  ON api.agent_conversations(user_id, updated_at DESC, message_count);

-- Full-text search on conversation titles
CREATE INDEX idx_agent_conversations_title_gin 
  ON api.agent_conversations USING gin(to_tsvector('english', coalesce(title, '')));

-- Covering index for message loading (enables index-only scans)
CREATE INDEX idx_agent_messages_conversation_covering 
  ON api.agent_messages(conversation_id, created_at ASC) 
  INCLUDE (content, role, agent_type, metadata);

-- Index for recent messages query
CREATE INDEX idx_agent_messages_conversation_recent 
  ON api.agent_messages(conversation_id, created_at DESC);

-- Full-text search on message content
CREATE INDEX idx_agent_messages_content_gin 
  ON api.agent_messages USING gin(to_tsvector('english', content));
```

### Query Optimizations

1. **Pagination Support**: Added `offset` parameter to `list_conversations` and `get_conversation` endpoints
2. **Column Selection**: Queries now select only needed columns instead of `SELECT *`
3. **Efficient Recent Messages**: New `get_recent_messages` method uses DESC ordering with LIMIT for context building
4. **Maximum Limits**: Enforced `MAX_MESSAGE_LIMIT = 500` to prevent memory issues

### API Changes

#### List Conversations
```
GET /api/conversations?user_id=xxx&limit=50&offset=0
```

Response now includes pagination metadata:
```json
{
  "conversations": [...],
  "total": 100,
  "limit": 50,
  "offset": 0,
  "has_more": true
}
```

#### Get Conversation
```
GET /api/conversations/{id}?user_id=xxx&message_limit=100&message_offset=0
```

---

## Streaming Latency Optimization (Task 23.2)

### Configuration Constants

```python
# Queue polling timeout (reduced from 50ms to 20ms)
QUEUE_POLL_TIMEOUT = 0.02

# Async sleep interval (reduced from 10ms to 5ms)
ASYNC_SLEEP_INTERVAL = 0.005

# Token batching settings
TOKEN_BATCH_WINDOW_MS = 10  # Batch tokens within 10ms window
TOKEN_BATCH_MAX_SIZE = 5    # Maximum tokens per batch

# Minimum SSE interval
MIN_SSE_INTERVAL_MS = 5
```

### Optimizations Applied

1. **Reduced Queue Polling**: Decreased from 50ms to 20ms for faster token delivery
2. **Token Batching**: Tokens arriving within 10ms are batched together to reduce SSE overhead
3. **Optimized Async Sleep**: Reduced from 10ms to 5ms when queue is empty
4. **Enhanced SSE Headers**: Added headers to disable buffering at all proxy levels

### SSE Response Headers

```python
headers = {
    "Cache-Control": "no-cache, no-store, must-revalidate",
    "Pragma": "no-cache",
    "Expires": "0",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",  # Nginx
    "X-Content-Type-Options": "nosniff",
    "Transfer-Encoding": "chunked",
}
```

---

## Performance Metrics

### Expected Improvements

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Queue poll latency | 50ms | 20ms | 60% faster |
| Async sleep interval | 10ms | 5ms | 50% faster |
| First token latency | ~100ms | ~50ms | ~50% faster |
| SSE overhead | High (per token) | Low (batched) | Reduced |

### Monitoring

Monitor these metrics in production:
- Time to first token (TTFT)
- Tokens per second throughput
- Database query execution time
- Memory usage during streaming

---

## Requirements Validated

- **Requirement 21.2**: Database queries optimized with proper indexes
- **Requirement 21.3**: Streaming optimized with reduced latency and token batching

---

## Future Improvements

1. **Connection Pooling**: Implement Supabase connection pooling for high concurrency
2. **Redis Caching**: Cache frequently accessed conversations
3. **Read Replicas**: Use read replicas for query distribution
4. **WebSocket Upgrade**: Consider WebSocket for bidirectional streaming
