-- =====================================================
-- AI Chat Schema Verification Script
-- =====================================================
-- Run this script in your Supabase SQL Editor to verify
-- that the AI chat tables are properly set up
-- =====================================================

-- =====================================================
-- 1. CHECK IF TABLES EXIST
-- =====================================================
SELECT 
  'Tables Exist Check' as test_name,
  COUNT(*) as tables_found,
  CASE 
    WHEN COUNT(*) = 2 THEN '✅ PASS'
    ELSE '❌ FAIL - Expected 2 tables'
  END as status
FROM information_schema.tables 
WHERE table_schema = 'api' 
AND table_name IN ('agent_conversations', 'agent_messages');

-- =====================================================
-- 2. CHECK TABLE STRUCTURE - agent_conversations
-- =====================================================
SELECT 
  'agent_conversations Structure' as test_name,
  column_name,
  data_type,
  is_nullable,
  column_default
FROM information_schema.columns
WHERE table_schema = 'api' 
AND table_name = 'agent_conversations'
ORDER BY ordinal_position;

-- =====================================================
-- 3. CHECK TABLE STRUCTURE - agent_messages
-- =====================================================
SELECT 
  'agent_messages Structure' as test_name,
  column_name,
  data_type,
  is_nullable,
  column_default
FROM information_schema.columns
WHERE table_schema = 'api' 
AND table_name = 'agent_messages'
ORDER BY ordinal_position;

-- =====================================================
-- 4. CHECK INDEXES
-- =====================================================
SELECT 
  'Indexes Check' as test_name,
  schemaname,
  tablename,
  indexname,
  indexdef
FROM pg_indexes
WHERE schemaname = 'api'
AND tablename IN ('agent_conversations', 'agent_messages')
ORDER BY tablename, indexname;

-- Expected indexes:
-- - idx_agent_conversations_user
-- - idx_agent_conversations_last_message
-- - idx_agent_messages_conversation
-- - idx_agent_messages_agent_type
-- - idx_agent_messages_role

-- =====================================================
-- 5. CHECK RLS IS ENABLED
-- =====================================================
SELECT 
  'RLS Enabled Check' as test_name,
  schemaname,
  tablename,
  rowsecurity as rls_enabled,
  CASE 
    WHEN rowsecurity = true THEN '✅ PASS'
    ELSE '❌ FAIL - RLS not enabled'
  END as status
FROM pg_tables
WHERE schemaname = 'api'
AND tablename IN ('agent_conversations', 'agent_messages');

-- =====================================================
-- 6. CHECK RLS POLICIES
-- =====================================================
SELECT 
  'RLS Policies Check' as test_name,
  schemaname,
  tablename,
  policyname,
  permissive,
  roles,
  cmd,
  qual,
  with_check
FROM pg_policies 
WHERE schemaname = 'api'
AND tablename IN ('agent_conversations', 'agent_messages')
ORDER BY tablename, policyname;

-- Expected policies for agent_conversations:
-- - Users can view own agent conversations (SELECT)
-- - Users can create own agent conversations (INSERT)
-- - Users can update own agent conversations (UPDATE)
-- - Users can delete own agent conversations (DELETE)

-- Expected policies for agent_messages:
-- - Users can view own agent messages (SELECT)
-- - Users can create agent messages in own conversations (INSERT)

-- =====================================================
-- 7. CHECK TRIGGERS
-- =====================================================
SELECT 
  'Triggers Check' as test_name,
  trigger_name,
  event_manipulation,
  event_object_table,
  action_statement,
  action_timing
FROM information_schema.triggers 
WHERE event_object_schema = 'api'
AND event_object_table IN ('agent_conversations', 'agent_messages')
ORDER BY event_object_table, trigger_name;

-- Expected triggers:
-- - update_agent_conversations_updated_at (BEFORE UPDATE)
-- - update_agent_conversation_on_message_trigger (AFTER INSERT on agent_messages)

-- =====================================================
-- 8. CHECK FOREIGN KEY CONSTRAINTS
-- =====================================================
SELECT 
  'Foreign Keys Check' as test_name,
  tc.table_name,
  kcu.column_name,
  ccu.table_name AS foreign_table_name,
  ccu.column_name AS foreign_column_name,
  rc.delete_rule
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
  AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
  AND ccu.table_schema = tc.table_schema
JOIN information_schema.referential_constraints AS rc
  ON rc.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
AND tc.table_schema = 'api'
AND tc.table_name IN ('agent_conversations', 'agent_messages');

-- Expected foreign keys:
-- - agent_conversations.user_id -> auth.users.id (CASCADE)
-- - agent_messages.conversation_id -> agent_conversations.id (CASCADE)

-- =====================================================
-- 9. CHECK CHECK CONSTRAINTS
-- =====================================================
SELECT 
  'Check Constraints' as test_name,
  tc.table_name,
  tc.constraint_name,
  cc.check_clause
FROM information_schema.table_constraints AS tc
JOIN information_schema.check_constraints AS cc
  ON tc.constraint_name = cc.constraint_name
WHERE tc.constraint_type = 'CHECK'
AND tc.table_schema = 'api'
AND tc.table_name IN ('agent_conversations', 'agent_messages');

-- Expected check constraints:
-- - agent_messages.role IN ('user', 'assistant')
-- - agent_messages.agent_type IN ('supervisor', 'invoices', 'appointments', ...)

-- =====================================================
-- 10. TEST TRIGGER FUNCTIONALITY
-- =====================================================
-- This section tests that triggers work correctly
-- Run these commands in sequence and verify the results

-- Step 1: Create a test conversation
DO $
DECLARE
  test_conversation_id UUID;
  test_user_id UUID;
  initial_message_count INTEGER;
  final_message_count INTEGER;
  initial_updated_at TIMESTAMP;
  final_updated_at TIMESTAMP;
BEGIN
  -- Get current user ID (or use a test user)
  test_user_id := auth.uid();
  
  -- Create test conversation
  INSERT INTO api.agent_conversations (user_id, title)
  VALUES (test_user_id, 'Test Conversation - DELETE ME')
  RETURNING id INTO test_conversation_id;
  
  -- Get initial state
  SELECT message_count, updated_at 
  INTO initial_message_count, initial_updated_at
  FROM api.agent_conversations 
  WHERE id = test_conversation_id;
  
  -- Wait a moment
  PERFORM pg_sleep(1);
  
  -- Add a test message (should trigger update)
  INSERT INTO api.agent_messages (conversation_id, content, role)
  VALUES (test_conversation_id, 'Test message', 'user');
  
  -- Get final state
  SELECT message_count, updated_at 
  INTO final_message_count, final_updated_at
  FROM api.agent_conversations 
  WHERE id = test_conversation_id;
  
  -- Verify trigger worked
  IF final_message_count = initial_message_count + 1 
     AND final_updated_at > initial_updated_at THEN
    RAISE NOTICE '✅ PASS - Trigger updated conversation metadata correctly';
    RAISE NOTICE 'Message count: % -> %', initial_message_count, final_message_count;
    RAISE NOTICE 'Updated at: % -> %', initial_updated_at, final_updated_at;
  ELSE
    RAISE NOTICE '❌ FAIL - Trigger did not update conversation metadata';
    RAISE NOTICE 'Message count: % -> %', initial_message_count, final_message_count;
    RAISE NOTICE 'Updated at: % -> %', initial_updated_at, final_updated_at;
  END IF;
  
  -- Clean up test data
  DELETE FROM api.agent_conversations WHERE id = test_conversation_id;
  RAISE NOTICE 'Test data cleaned up';
END $;

-- =====================================================
-- 11. TEST RLS POLICIES
-- =====================================================
-- This section tests that RLS policies work correctly
-- Note: This requires being authenticated as a user

-- Test 1: Try to create a conversation for current user (should succeed)
DO $
DECLARE
  test_conversation_id UUID;
  test_user_id UUID;
BEGIN
  test_user_id := auth.uid();
  
  IF test_user_id IS NULL THEN
    RAISE NOTICE '⚠️  WARNING - Not authenticated, skipping RLS test';
  ELSE
    -- Should succeed
    INSERT INTO api.agent_conversations (user_id, title)
    VALUES (test_user_id, 'RLS Test - DELETE ME')
    RETURNING id INTO test_conversation_id;
    
    RAISE NOTICE '✅ PASS - Can create own conversation';
    
    -- Clean up
    DELETE FROM api.agent_conversations WHERE id = test_conversation_id;
  END IF;
END $;

-- =====================================================
-- 12. SUMMARY
-- =====================================================
SELECT 
  'Schema Setup Summary' as summary,
  (SELECT COUNT(*) FROM information_schema.tables 
   WHERE table_schema = 'api' 
   AND table_name IN ('agent_conversations', 'agent_messages')) as tables_created,
  (SELECT COUNT(*) FROM pg_policies 
   WHERE schemaname = 'api' 
   AND tablename IN ('agent_conversations', 'agent_messages')) as policies_created,
  (SELECT COUNT(*) FROM information_schema.triggers 
   WHERE event_object_schema = 'api' 
   AND event_object_table IN ('agent_conversations', 'agent_messages')) as triggers_created,
  (SELECT COUNT(*) FROM pg_indexes 
   WHERE schemaname = 'api' 
   AND tablename IN ('agent_conversations', 'agent_messages')) as indexes_created;

-- =====================================================
-- Expected Results:
-- - tables_created: 2
-- - policies_created: 6 (4 for conversations, 2 for messages)
-- - triggers_created: 2 (1 for updated_at, 1 for message count)
-- - indexes_created: 5+
-- =====================================================
