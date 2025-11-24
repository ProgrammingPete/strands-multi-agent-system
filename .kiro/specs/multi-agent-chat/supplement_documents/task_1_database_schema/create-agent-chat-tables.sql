-- =====================================================
-- AGENT CONVERSATIONS TABLE (AI Chat History)
-- =====================================================
-- Migration: create_agent_chat_tables
-- Date: 2025-11-24
-- Description: Creates the agent_conversations and agent_messages tables
--              with RLS policies, triggers, and indexes for the AI chat system
-- =====================================================

CREATE TABLE IF NOT EXISTS api.agent_conversations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  title TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  last_message_at TIMESTAMP WITH TIME ZONE,
  message_count INTEGER DEFAULT 0,
  metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_agent_conversations_user ON api.agent_conversations(user_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_conversations_last_message ON api.agent_conversations(last_message_at DESC);

-- =====================================================
-- AGENT MESSAGES TABLE (AI Chat Messages)
-- =====================================================
CREATE TABLE IF NOT EXISTS api.agent_messages (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  conversation_id UUID NOT NULL REFERENCES api.agent_conversations(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
  agent_type TEXT CHECK (agent_type IN ('supervisor', 'invoices', 'appointments', 'projects', 'proposals', 'contacts', 'reviews', 'campaigns', 'tasks', 'settings')),
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_messages_conversation ON api.agent_messages(conversation_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_messages_agent_type ON api.agent_messages(agent_type) WHERE agent_type IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_agent_messages_role ON api.agent_messages(role);

-- =====================================================
-- AGENT TABLES - ROW LEVEL SECURITY
-- =====================================================
ALTER TABLE api.agent_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE api.agent_messages ENABLE ROW LEVEL SECURITY;

-- Users can only see their own AI conversations
CREATE POLICY "Users can view own agent conversations"
  ON api.agent_conversations FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can create own agent conversations"
  ON api.agent_conversations FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own agent conversations"
  ON api.agent_conversations FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own agent conversations"
  ON api.agent_conversations FOR DELETE
  USING (auth.uid() = user_id);

-- Users can only see messages in their AI conversations
CREATE POLICY "Users can view own agent messages"
  ON api.agent_messages FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM api.agent_conversations
      WHERE agent_conversations.id = agent_messages.conversation_id
      AND agent_conversations.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can create agent messages in own conversations"
  ON api.agent_messages FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM api.agent_conversations
      WHERE agent_conversations.id = agent_messages.conversation_id
      AND agent_conversations.user_id = auth.uid()
    )
  );

-- =====================================================
-- AGENT TABLES - TRIGGERS
-- =====================================================

-- Trigger for agent_conversations updated_at
CREATE TRIGGER update_agent_conversations_updated_at BEFORE UPDATE ON api.agent_conversations
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to update conversation metadata on new message
CREATE OR REPLACE FUNCTION update_agent_conversation_on_message()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE api.agent_conversations
  SET 
    updated_at = NOW(),
    last_message_at = NEW.created_at,
    message_count = message_count + 1
  WHERE id = NEW.conversation_id;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update conversation when message is added
CREATE TRIGGER update_agent_conversation_on_message_trigger
  AFTER INSERT ON api.agent_messages
  FOR EACH ROW
  EXECUTE FUNCTION update_agent_conversation_on_message();
