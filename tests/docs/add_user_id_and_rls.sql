-- ============================================================================
-- Production Security Migration: Add user_id and RLS Policies
-- ============================================================================
--
-- This script prepares the database for production by:
-- 1. Adding user_id columns to all business tables
-- 2. Enabling Row Level Security (RLS)
-- 3. Creating policies for user data isolation
--
-- Run this in: Supabase Dashboard > SQL Editor > New Query
--
-- ⚠️  IMPORTANT: This is a breaking change!
-- After running this, you MUST update your backend to use user JWTs
-- instead of the secret key, or all operations will fail.
-- ============================================================================

-- ============================================================================
-- STEP 1: Add user_id columns to all tables
-- ============================================================================

-- Add user_id to invoices
ALTER TABLE api.invoices 
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id);

-- Add user_id to projects (if not exists)
ALTER TABLE api.projects 
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id);

-- Add user_id to appointments (if not exists)
ALTER TABLE api.appointments 
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id);

-- Add user_id to proposals (if not exists)
ALTER TABLE api.proposals 
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id);

-- Add user_id to contacts (if not exists)
ALTER TABLE api.contacts 
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id);

-- Add user_id to reviews (if not exists)
ALTER TABLE api.reviews 
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id);

-- Add user_id to campaigns (if not exists)
ALTER TABLE api.campaigns 
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id);

-- Add user_id to tasks (if not exists)
ALTER TABLE api.tasks 
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id);

-- Add user_id to goals (if not exists)
ALTER TABLE api.goals 
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id);

-- ============================================================================
-- STEP 2: Backfill existing data with system user
-- ============================================================================
-- 
-- Option A: Use a specific system user UUID
-- Option B: Assign to first user in auth.users
-- Option C: Leave NULL and handle in application
--
-- Uncomment ONE of the following:
-- ============================================================================

-- Option A: System user (recommended for testing)
-- UPDATE api.invoices SET user_id = '00000000-0000-0000-0000-000000000000' WHERE user_id IS NULL;
-- UPDATE api.projects SET user_id = '00000000-0000-0000-0000-000000000000' WHERE user_id IS NULL;
-- UPDATE api.appointments SET user_id = '00000000-0000-0000-0000-000000000000' WHERE user_id IS NULL;
-- UPDATE api.proposals SET user_id = '00000000-0000-0000-0000-000000000000' WHERE user_id IS NULL;
-- UPDATE api.contacts SET user_id = '00000000-0000-0000-0000-000000000000' WHERE user_id IS NULL;
-- UPDATE api.reviews SET user_id = '00000000-0000-0000-0000-000000000000' WHERE user_id IS NULL;
-- UPDATE api.campaigns SET user_id = '00000000-0000-0000-0000-000000000000' WHERE user_id IS NULL;
-- UPDATE api.tasks SET user_id = '00000000-0000-0000-0000-000000000000' WHERE user_id IS NULL;
-- UPDATE api.goals SET user_id = '00000000-0000-0000-0000-000000000000' WHERE user_id IS NULL;

-- Option B: Assign to first user (recommended for production)
-- DO $$
-- DECLARE
--   first_user_id UUID;
-- BEGIN
--   SELECT id INTO first_user_id FROM auth.users ORDER BY created_at LIMIT 1;
--   
--   UPDATE api.invoices SET user_id = first_user_id WHERE user_id IS NULL;
--   UPDATE api.projects SET user_id = first_user_id WHERE user_id IS NULL;
--   UPDATE api.appointments SET user_id = first_user_id WHERE user_id IS NULL;
--   UPDATE api.proposals SET user_id = first_user_id WHERE user_id IS NULL;
--   UPDATE api.contacts SET user_id = first_user_id WHERE user_id IS NULL;
--   UPDATE api.reviews SET user_id = first_user_id WHERE user_id IS NULL;
--   UPDATE api.campaigns SET user_id = first_user_id WHERE user_id IS NULL;
--   UPDATE api.tasks SET user_id = first_user_id WHERE user_id IS NULL;
--   UPDATE api.goals SET user_id = first_user_id WHERE user_id IS NULL;
-- END $$;

-- ============================================================================
-- STEP 3: Make user_id required (after backfill)
-- ============================================================================

-- Uncomment after backfilling data:
-- ALTER TABLE api.invoices ALTER COLUMN user_id SET NOT NULL;
-- ALTER TABLE api.projects ALTER COLUMN user_id SET NOT NULL;
-- ALTER TABLE api.appointments ALTER COLUMN user_id SET NOT NULL;
-- ALTER TABLE api.proposals ALTER COLUMN user_id SET NOT NULL;
-- ALTER TABLE api.contacts ALTER COLUMN user_id SET NOT NULL;
-- ALTER TABLE api.reviews ALTER COLUMN user_id SET NOT NULL;
-- ALTER TABLE api.campaigns ALTER COLUMN user_id SET NOT NULL;
-- ALTER TABLE api.tasks ALTER COLUMN user_id SET NOT NULL;
-- ALTER TABLE api.goals ALTER COLUMN user_id SET NOT NULL;

-- ============================================================================
-- STEP 4: Create indexes for performance
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_invoices_user_id ON api.invoices(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON api.projects(user_id);
CREATE INDEX IF NOT EXISTS idx_appointments_user_id ON api.appointments(user_id);
CREATE INDEX IF NOT EXISTS idx_proposals_user_id ON api.proposals(user_id);
CREATE INDEX IF NOT EXISTS idx_contacts_user_id ON api.contacts(user_id);
CREATE INDEX IF NOT EXISTS idx_reviews_user_id ON api.reviews(user_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_user_id ON api.campaigns(user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON api.tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_goals_user_id ON api.goals(user_id);

-- ============================================================================
-- STEP 5: Enable RLS on all tables
-- ============================================================================

ALTER TABLE api.invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE api.projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE api.appointments ENABLE ROW LEVEL SECURITY;
ALTER TABLE api.proposals ENABLE ROW LEVEL SECURITY;
ALTER TABLE api.contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE api.reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE api.campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE api.tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE api.goals ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- STEP 6: Create RLS Policies for Invoices
-- ============================================================================

-- SELECT policy
CREATE POLICY "Users can view own invoices"
ON api.invoices FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

-- INSERT policy
CREATE POLICY "Users can create own invoices"
ON api.invoices FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

-- UPDATE policy
CREATE POLICY "Users can update own invoices"
ON api.invoices FOR UPDATE
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- DELETE policy
CREATE POLICY "Users can delete own invoices"
ON api.invoices FOR DELETE
TO authenticated
USING (auth.uid() = user_id);

-- ============================================================================
-- STEP 7: Create RLS Policies for Other Tables
-- ============================================================================
-- Repeat the same pattern for projects, appointments, proposals, etc.
-- Example for projects:

CREATE POLICY "Users can view own projects"
ON api.projects FOR SELECT TO authenticated
USING (auth.uid() = user_id);

CREATE POLICY "Users can create own projects"
ON api.projects FOR INSERT TO authenticated
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own projects"
ON api.projects FOR UPDATE TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own projects"
ON api.projects FOR DELETE TO authenticated
USING (auth.uid() = user_id);

-- Repeat for: appointments, proposals, contacts, reviews, campaigns, tasks, goals

-- ============================================================================
-- STEP 8: Verification Queries
-- ============================================================================

-- Check that user_id columns exist
SELECT 
  table_name,
  column_name,
  data_type,
  is_nullable
FROM information_schema.columns
WHERE table_schema = 'api'
AND column_name = 'user_id'
ORDER BY table_name;

-- Check RLS is enabled
SELECT 
  schemaname,
  tablename,
  rowsecurity as rls_enabled
FROM pg_tables
WHERE schemaname = 'api'
ORDER BY tablename;

-- Check policies exist
SELECT 
  schemaname,
  tablename,
  policyname,
  permissive,
  roles,
  cmd
FROM pg_policies
WHERE schemaname = 'api'
ORDER BY tablename, policyname;

-- ============================================================================
-- Success message
-- ============================================================================

DO $$
BEGIN
  RAISE NOTICE '============================================================';
  RAISE NOTICE 'Production Security Migration Complete!';
  RAISE NOTICE '============================================================';
  RAISE NOTICE '';
  RAISE NOTICE 'Next steps:';
  RAISE NOTICE '1. Update backend code to use user JWTs instead of secret key';
  RAISE NOTICE '2. Update frontend to send user JWTs to backend';
  RAISE NOTICE '3. Test with multiple users to verify data isolation';
  RAISE NOTICE '4. Remove secret key from production environment';
  RAISE NOTICE '';
  RAISE NOTICE '⚠️  WARNING: Using secret key will now bypass RLS!';
  RAISE NOTICE '   Only use secret key for admin operations.';
  RAISE NOTICE '============================================================';
END $$;
