-- ============================================================================
-- Migration: Add user_id columns and RLS policies for production security
-- ============================================================================
-- This migration adds user_id columns to all api schema tables, creates
-- foreign key references to auth.users(id), creates indexes for performance,
-- enables Row Level Security (RLS), and creates policies for data isolation.
--
-- Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 3.1, 3.2, 3.3, 3.4, 10.1-10.7
-- ============================================================================

-- ============================================================================
-- PART 1: Add user_id columns to all api schema tables
-- Requirements: 2.1, 2.2, 2.7, 10.1, 10.2
-- ============================================================================

-- Add user_id column to invoices table
ALTER TABLE api.invoices
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id);

-- Add user_id column to projects table
ALTER TABLE api.projects
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id);

-- Add user_id column to appointments table
ALTER TABLE api.appointments
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id);

-- Add user_id column to proposals table
ALTER TABLE api.proposals
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id);

-- Add user_id column to contacts table
ALTER TABLE api.contacts
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id);

-- Add user_id column to reviews table
ALTER TABLE api.reviews
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id);

-- Add user_id column to campaigns table
ALTER TABLE api.campaigns
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id);

-- Add user_id column to tasks table
ALTER TABLE api.tasks
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id);

-- Add user_id column to goals table
ALTER TABLE api.goals
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id);

-- ============================================================================
-- PART 2: Create indexes on all user_id columns for performance
-- Requirements: 2.7, 10.2
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
-- PART 3: Enable RLS and create policies for all tables
-- Requirements: 2.3, 2.4, 2.5, 2.6, 10.3, 10.4
-- ============================================================================

-- -----------------------------------------------------------------------------
-- INVOICES TABLE RLS
-- -----------------------------------------------------------------------------
ALTER TABLE api.invoices ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own invoices" ON api.invoices;
CREATE POLICY "Users can view own invoices"
ON api.invoices FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can create own invoices" ON api.invoices;
CREATE POLICY "Users can create own invoices"
ON api.invoices FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own invoices" ON api.invoices;
CREATE POLICY "Users can update own invoices"
ON api.invoices FOR UPDATE
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own invoices" ON api.invoices;
CREATE POLICY "Users can delete own invoices"
ON api.invoices FOR DELETE
TO authenticated
USING (auth.uid() = user_id);

-- -----------------------------------------------------------------------------
-- PROJECTS TABLE RLS
-- -----------------------------------------------------------------------------
ALTER TABLE api.projects ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own projects" ON api.projects;
CREATE POLICY "Users can view own projects"
ON api.projects FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can create own projects" ON api.projects;
CREATE POLICY "Users can create own projects"
ON api.projects FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own projects" ON api.projects;
CREATE POLICY "Users can update own projects"
ON api.projects FOR UPDATE
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own projects" ON api.projects;
CREATE POLICY "Users can delete own projects"
ON api.projects FOR DELETE
TO authenticated
USING (auth.uid() = user_id);

-- -----------------------------------------------------------------------------
-- APPOINTMENTS TABLE RLS
-- -----------------------------------------------------------------------------
ALTER TABLE api.appointments ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own appointments" ON api.appointments;
CREATE POLICY "Users can view own appointments"
ON api.appointments FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can create own appointments" ON api.appointments;
CREATE POLICY "Users can create own appointments"
ON api.appointments FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own appointments" ON api.appointments;
CREATE POLICY "Users can update own appointments"
ON api.appointments FOR UPDATE
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own appointments" ON api.appointments;
CREATE POLICY "Users can delete own appointments"
ON api.appointments FOR DELETE
TO authenticated
USING (auth.uid() = user_id);

-- -----------------------------------------------------------------------------
-- PROPOSALS TABLE RLS
-- -----------------------------------------------------------------------------
ALTER TABLE api.proposals ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own proposals" ON api.proposals;
CREATE POLICY "Users can view own proposals"
ON api.proposals FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can create own proposals" ON api.proposals;
CREATE POLICY "Users can create own proposals"
ON api.proposals FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own proposals" ON api.proposals;
CREATE POLICY "Users can update own proposals"
ON api.proposals FOR UPDATE
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own proposals" ON api.proposals;
CREATE POLICY "Users can delete own proposals"
ON api.proposals FOR DELETE
TO authenticated
USING (auth.uid() = user_id);

-- -----------------------------------------------------------------------------
-- CONTACTS TABLE RLS
-- -----------------------------------------------------------------------------
ALTER TABLE api.contacts ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own contacts" ON api.contacts;
CREATE POLICY "Users can view own contacts"
ON api.contacts FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can create own contacts" ON api.contacts;
CREATE POLICY "Users can create own contacts"
ON api.contacts FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own contacts" ON api.contacts;
CREATE POLICY "Users can update own contacts"
ON api.contacts FOR UPDATE
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own contacts" ON api.contacts;
CREATE POLICY "Users can delete own contacts"
ON api.contacts FOR DELETE
TO authenticated
USING (auth.uid() = user_id);

-- -----------------------------------------------------------------------------
-- REVIEWS TABLE RLS
-- -----------------------------------------------------------------------------
ALTER TABLE api.reviews ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own reviews" ON api.reviews;
CREATE POLICY "Users can view own reviews"
ON api.reviews FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can create own reviews" ON api.reviews;
CREATE POLICY "Users can create own reviews"
ON api.reviews FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own reviews" ON api.reviews;
CREATE POLICY "Users can update own reviews"
ON api.reviews FOR UPDATE
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own reviews" ON api.reviews;
CREATE POLICY "Users can delete own reviews"
ON api.reviews FOR DELETE
TO authenticated
USING (auth.uid() = user_id);

-- -----------------------------------------------------------------------------
-- CAMPAIGNS TABLE RLS
-- -----------------------------------------------------------------------------
ALTER TABLE api.campaigns ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own campaigns" ON api.campaigns;
CREATE POLICY "Users can view own campaigns"
ON api.campaigns FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can create own campaigns" ON api.campaigns;
CREATE POLICY "Users can create own campaigns"
ON api.campaigns FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own campaigns" ON api.campaigns;
CREATE POLICY "Users can update own campaigns"
ON api.campaigns FOR UPDATE
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own campaigns" ON api.campaigns;
CREATE POLICY "Users can delete own campaigns"
ON api.campaigns FOR DELETE
TO authenticated
USING (auth.uid() = user_id);

-- -----------------------------------------------------------------------------
-- TASKS TABLE RLS
-- -----------------------------------------------------------------------------
ALTER TABLE api.tasks ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own tasks" ON api.tasks;
CREATE POLICY "Users can view own tasks"
ON api.tasks FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can create own tasks" ON api.tasks;
CREATE POLICY "Users can create own tasks"
ON api.tasks FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own tasks" ON api.tasks;
CREATE POLICY "Users can update own tasks"
ON api.tasks FOR UPDATE
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own tasks" ON api.tasks;
CREATE POLICY "Users can delete own tasks"
ON api.tasks FOR DELETE
TO authenticated
USING (auth.uid() = user_id);

-- -----------------------------------------------------------------------------
-- GOALS TABLE RLS
-- -----------------------------------------------------------------------------
ALTER TABLE api.goals ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own goals" ON api.goals;
CREATE POLICY "Users can view own goals"
ON api.goals FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can create own goals" ON api.goals;
CREATE POLICY "Users can create own goals"
ON api.goals FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own goals" ON api.goals;
CREATE POLICY "Users can update own goals"
ON api.goals FOR UPDATE
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own goals" ON api.goals;
CREATE POLICY "Users can delete own goals"
ON api.goals FOR DELETE
TO authenticated
USING (auth.uid() = user_id);

-- ============================================================================
-- PART 4: Grant schema permissions to Postgres roles
-- Requirements: 3.1, 3.2, 3.3, 3.4
-- ============================================================================

-- Grant USAGE on api schema to authenticated, anon, and service_role
GRANT USAGE ON SCHEMA api TO authenticated;
GRANT USAGE ON SCHEMA api TO anon;
GRANT USAGE ON SCHEMA api TO service_role;

-- Grant table permissions to authenticated role
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA api TO authenticated;

-- Grant table permissions to anon role (read-only for public data if needed)
GRANT SELECT ON ALL TABLES IN SCHEMA api TO anon;

-- Grant full permissions to service_role (for admin operations)
GRANT ALL ON ALL TABLES IN SCHEMA api TO service_role;

-- Grant sequence permissions (for auto-increment columns)
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA api TO authenticated;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA api TO anon;
GRANT ALL ON ALL SEQUENCES IN SCHEMA api TO service_role;

-- Grant function permissions
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA api TO authenticated;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA api TO anon;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA api TO service_role;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA api
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO authenticated;

ALTER DEFAULT PRIVILEGES IN SCHEMA api
GRANT SELECT ON TABLES TO anon;

ALTER DEFAULT PRIVILEGES IN SCHEMA api
GRANT ALL ON TABLES TO service_role;

-- Set default privileges for future sequences
ALTER DEFAULT PRIVILEGES IN SCHEMA api
GRANT USAGE, SELECT ON SEQUENCES TO authenticated;

ALTER DEFAULT PRIVILEGES IN SCHEMA api
GRANT USAGE, SELECT ON SEQUENCES TO anon;

ALTER DEFAULT PRIVILEGES IN SCHEMA api
GRANT ALL ON SEQUENCES TO service_role;

-- ============================================================================
-- PART 5: Verification queries
-- Requirements: 10.5
-- ============================================================================

-- Verify user_id columns exist on all tables
SELECT 
    table_name, 
    column_name, 
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'api' 
AND column_name = 'user_id'
ORDER BY table_name;

-- Verify RLS is enabled on all tables
SELECT 
    schemaname,
    tablename, 
    rowsecurity
FROM pg_tables
WHERE schemaname = 'api'
ORDER BY tablename;

-- Verify RLS policies exist for all tables
SELECT 
    schemaname,
    tablename, 
    policyname, 
    cmd,
    roles
FROM pg_policies
WHERE schemaname = 'api'
ORDER BY tablename, cmd;

-- Verify indexes exist on user_id columns
SELECT 
    schemaname,
    tablename,
    indexname
FROM pg_indexes
WHERE schemaname = 'api'
AND indexname LIKE '%user_id%'
ORDER BY tablename;

-- ============================================================================
-- PART 6: Backfill options (run one of these after migration)
-- Requirements: 2.8, 10.6
-- ============================================================================

-- Option A: Assign all existing data to a system user
-- Replace 'YOUR_SYSTEM_USER_UUID' with actual system user UUID
-- UPDATE api.invoices SET user_id = 'YOUR_SYSTEM_USER_UUID' WHERE user_id IS NULL;
-- UPDATE api.projects SET user_id = 'YOUR_SYSTEM_USER_UUID' WHERE user_id IS NULL;
-- UPDATE api.appointments SET user_id = 'YOUR_SYSTEM_USER_UUID' WHERE user_id IS NULL;
-- UPDATE api.proposals SET user_id = 'YOUR_SYSTEM_USER_UUID' WHERE user_id IS NULL;
-- UPDATE api.contacts SET user_id = 'YOUR_SYSTEM_USER_UUID' WHERE user_id IS NULL;
-- UPDATE api.reviews SET user_id = 'YOUR_SYSTEM_USER_UUID' WHERE user_id IS NULL;
-- UPDATE api.campaigns SET user_id = 'YOUR_SYSTEM_USER_UUID' WHERE user_id IS NULL;
-- UPDATE api.tasks SET user_id = 'YOUR_SYSTEM_USER_UUID' WHERE user_id IS NULL;
-- UPDATE api.goals SET user_id = 'YOUR_SYSTEM_USER_UUID' WHERE user_id IS NULL;

-- Option B: Assign existing data to the first user in auth.users
-- WITH first_user AS (
--     SELECT id FROM auth.users ORDER BY created_at LIMIT 1
-- )
-- UPDATE api.invoices SET user_id = (SELECT id FROM first_user) WHERE user_id IS NULL;
-- ... repeat for all tables

-- ============================================================================
-- PART 7: Make user_id NOT NULL (run after backfill is complete)
-- Requirements: 2.8
-- ============================================================================

-- IMPORTANT: Only run these after all existing data has user_id values
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
-- SUCCESS MESSAGE
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Migration completed successfully!';
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '1. Review verification query results above';
    RAISE NOTICE '2. Choose and run a backfill option (Part 6) if you have existing data';
    RAISE NOTICE '3. After backfill, run Part 7 to make user_id NOT NULL';
    RAISE NOTICE '4. Update backend code to use user-scoped clients';
    RAISE NOTICE '============================================================';
END $$;
