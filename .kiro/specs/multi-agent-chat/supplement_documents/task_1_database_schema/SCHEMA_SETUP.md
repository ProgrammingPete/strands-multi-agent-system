# AI Chat Database Schema Setup

## Overview

The database schema for the multi-agent chat system has been defined in:
`src/supabase/functions/server/schema.sql`

The schema includes two new tables specifically for AI chat:
- `api.agent_conversations` - Stores AI chat conversation metadata
- `api.agent_messages` - Stores individual messages in AI chat conversations

## Tables Created

### api.agent_conversations
- Stores conversation sessions between users and the AI agent system
- Includes metadata like title, message count, and last message timestamp
- Linked to auth.users via user_id

### api.agent_messages
- Stores individual messages (both user and assistant)
- Includes role (user/assistant), agent_type, and metadata
- Linked to agent_conversations via conversation_id

## Security Features

### Row Level Security (RLS)
Both tables have RLS enabled with policies that ensure:
- Users can only view their own conversations
- Users can only create messages in their own conversations
- Users can update/delete their own conversations

### Triggers
- `update_agent_conversations_updated_at` - Auto-updates the updated_at timestamp
- `update_agent_conversation_on_message_trigger` - Auto-updates conversation metadata when new messages are added

## How to Apply the Schema

### Option 1: Supabase Dashboard (Recommended)
1. Log in to your Supabase project dashboard
2. Navigate to the SQL Editor
3. Copy the entire contents of `src/supabase/functions/server/schema.sql`
4. Paste into the SQL Editor
5. Click "Run" to execute

### Option 2: Supabase CLI
```bash
# If you have Supabase CLI installed
supabase db push

# Or run the SQL file directly
psql -h <your-db-host> -U postgres -d postgres -f src/supabase/functions/server/schema.sql
```

### Option 3: Using the Supabase Client
The schema can also be applied programmatically, but this is not recommended for initial setup.

## Verification

After running the schema, verify the tables exist by running:

```sql
-- Check if tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'api' 
AND table_name IN ('agent_conversations', 'agent_messages');

-- Check RLS policies
SELECT schemaname, tablename, policyname 
FROM pg_policies 
WHERE tablename IN ('agent_conversations', 'agent_messages');

-- Check triggers
SELECT trigger_name, event_manipulation, event_object_table 
FROM information_schema.triggers 
WHERE event_object_table IN ('agent_conversations', 'agent_messages');
```

## Testing RLS Policies

To test that RLS policies are working correctly:

```sql
-- Test as authenticated user (replace with actual user_id)
SET LOCAL role authenticated;
SET LOCAL request.jwt.claims TO '{"sub": "test-user-id"}';

-- Try to create a conversation
INSERT INTO api.agent_conversations (user_id, title) 
VALUES ('test-user-id', 'Test Conversation');

-- Try to view conversations (should only see own)
SELECT * FROM api.agent_conversations;

-- Try to create a message
INSERT INTO api.agent_messages (conversation_id, content, role) 
VALUES ('<conversation-id>', 'Test message', 'user');
```

## Testing Triggers

To test that triggers are working:

```sql
-- Create a conversation
INSERT INTO api.agent_conversations (user_id, title) 
VALUES (auth.uid(), 'Test Conversation')
RETURNING id;

-- Add a message (should auto-update conversation metadata)
INSERT INTO api.agent_messages (conversation_id, content, role) 
VALUES ('<conversation-id-from-above>', 'Hello', 'user');

-- Verify conversation was updated
SELECT message_count, last_message_at, updated_at 
FROM api.agent_conversations 
WHERE id = '<conversation-id-from-above>';
-- Should show message_count = 1 and updated timestamps
```

## Next Steps

Once the schema is applied and verified:
1. ✅ Tables created
2. ✅ RLS policies active
3. ✅ Triggers working
4. Move to Phase 2: Backend implementation (Task 2)

## Notes

- The schema is idempotent - it uses `IF NOT EXISTS` clauses, so it's safe to run multiple times
- The existing `api.conversations` table is for client inbox messages, NOT AI chat
- The new `api.agent_conversations` table is specifically for AI chat sessions
- Both tables coexist and serve different purposes
