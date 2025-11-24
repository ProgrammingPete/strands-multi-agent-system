-- =====================================================
-- Enable RLS and Create Policies for API Schema Tables
-- =====================================================
-- Migration: enable_rls_and_policies_api_schema
-- Date: 2025-11-24
-- Description: Enables Row Level Security on all business tables
--              in the api schema and creates policies that allow
--              authenticated users to access all data.
-- =====================================================

-- =====================================================
-- CONTACTS TABLE
-- =====================================================
ALTER TABLE api.contacts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Enable all for authenticated users" ON api.contacts
  FOR ALL USING (auth.role() = 'authenticated');

-- =====================================================
-- PROJECTS TABLE
-- =====================================================
ALTER TABLE api.projects ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Enable all for authenticated users" ON api.projects
  FOR ALL USING (auth.role() = 'authenticated');

-- =====================================================
-- INVOICES TABLE
-- =====================================================
ALTER TABLE api.invoices ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Enable all for authenticated users" ON api.invoices
  FOR ALL USING (auth.role() = 'authenticated');

-- =====================================================
-- PROPOSALS TABLE
-- =====================================================
ALTER TABLE api.proposals ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Enable all for authenticated users" ON api.proposals
  FOR ALL USING (auth.role() = 'authenticated');

-- =====================================================
-- APPOINTMENTS TABLE
-- =====================================================
ALTER TABLE api.appointments ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Enable all for authenticated users" ON api.appointments
  FOR ALL USING (auth.role() = 'authenticated');

-- =====================================================
-- REVIEWS TABLE
-- =====================================================
ALTER TABLE api.reviews ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Enable all for authenticated users" ON api.reviews
  FOR ALL USING (auth.role() = 'authenticated');

-- =====================================================
-- CAMPAIGNS TABLE
-- =====================================================
ALTER TABLE api.campaigns ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Enable all for authenticated users" ON api.campaigns
  FOR ALL USING (auth.role() = 'authenticated');

-- =====================================================
-- CONVERSATIONS TABLE (Inbox)
-- =====================================================
ALTER TABLE api.conversations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Enable all for authenticated users" ON api.conversations
  FOR ALL USING (auth.role() = 'authenticated');

-- =====================================================
-- TASKS TABLE
-- =====================================================
ALTER TABLE api.tasks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Enable all for authenticated users" ON api.tasks
  FOR ALL USING (auth.role() = 'authenticated');

-- =====================================================
-- GOALS TABLE
-- =====================================================
ALTER TABLE api.goals ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Enable all for authenticated users" ON api.goals
  FOR ALL USING (auth.role() = 'authenticated');
