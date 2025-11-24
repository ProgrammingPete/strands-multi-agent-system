# Database Schema - Task 1

This folder contains the SQL migrations and verification scripts for the AI chat database schema.

## Files

### Migration Scripts (Applied)

1. **create-agent-chat-tables.sql**
   - Creates `api.agent_conversations` table
   - Creates `api.agent_messages` table
   - Adds indexes for performance
   - Enables RLS with user-specific policies
   - Creates triggers for automatic metadata updates
   - **Status**: ✅ Applied on 2025-11-24

2. **enable-rls-business-tables.sql**
   - Enables Row Level Security on all business tables in `api` schema
   - Creates policies allowing authenticated users to access data
   - Covers: contacts, projects, invoices, proposals, appointments, reviews, campaigns, conversations, tasks, goals
   - **Status**: ✅ Applied on 2025-11-24

### Verification Scripts

3. **verify-schema.sql**
   - Comprehensive verification script to check:
     - Table existence
     - Column structure
     - Indexes
     - RLS status
     - RLS policies
     - Triggers
     - Foreign key constraints
     - Check constraints
   - Run this in Supabase SQL Editor to verify setup

## Schema Overview

### Agent Chat Tables

#### `api.agent_conversations`
- Stores conversation metadata for AI chat sessions
- User-specific access via RLS
- Auto-updates `updated_at`, `last_message_at`, and `message_count`

#### `api.agent_messages`
- Stores individual chat messages
- Linked to conversations via foreign key
- Supports both user and assistant messages
- Tracks which agent handled the message

### Security Model

- **Agent chat tables**: User-specific access (users can only see their own data)
- **Business tables**: Authenticated user access (all authenticated users can access all data)

### Automation

All tables have triggers for:
- Auto-updating `updated_at` timestamp on modifications
- Auto-updating conversation metadata when messages are added

### Performance

All tables have appropriate indexes for:
- Primary key lookups
- Foreign key relationships
- Common query patterns (status, dates, user_id)

## Verification

To verify the schema is correctly set up, run:

```sql
-- Check all tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'api' 
ORDER BY table_name;

-- Check RLS is enabled
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'api';

-- Check policies exist
SELECT tablename, COUNT(*) as policy_count 
FROM pg_policies 
WHERE schemaname = 'api' 
GROUP BY tablename;
```

Or run the complete verification script: `verify-schema.sql`
