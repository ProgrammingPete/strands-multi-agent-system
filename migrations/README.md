# Database Migrations

This directory contains SQL migration scripts for the Canvalo multi-agent system.

## Migration Scripts

### add_user_id_and_rls.sql

This migration adds user_id columns and Row Level Security (RLS) policies to all api schema tables for production security.

**What it does:**
1. Adds `user_id` columns to all 9 api schema tables (invoices, projects, appointments, proposals, contacts, reviews, campaigns, tasks, goals)
2. Creates foreign key references to `auth.users(id)`
3. Creates indexes on all `user_id` columns for performance
4. Enables RLS on all tables
5. Creates SELECT, INSERT, UPDATE, DELETE policies using `auth.uid() = user_id`
6. Grants schema permissions to `authenticated`, `anon`, and `service_role` roles

**How to run:**
1. Open the Supabase SQL Editor for your project
2. Copy the contents of `add_user_id_and_rls.sql`
3. Execute the script
4. Review the verification query results
5. If you have existing data, run one of the backfill options (Part 6)
6. After backfill, run Part 7 to make `user_id` NOT NULL

**Requirements addressed:**
- 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8
- 3.1, 3.2, 3.3, 3.4
- 10.1, 10.2, 10.3, 10.4, 10.5, 10.6

## Rollback

To rollback the migration:

```sql
-- Disable RLS on all tables
ALTER TABLE api.invoices DISABLE ROW LEVEL SECURITY;
ALTER TABLE api.projects DISABLE ROW LEVEL SECURITY;
ALTER TABLE api.appointments DISABLE ROW LEVEL SECURITY;
ALTER TABLE api.proposals DISABLE ROW LEVEL SECURITY;
ALTER TABLE api.contacts DISABLE ROW LEVEL SECURITY;
ALTER TABLE api.reviews DISABLE ROW LEVEL SECURITY;
ALTER TABLE api.campaigns DISABLE ROW LEVEL SECURITY;
ALTER TABLE api.tasks DISABLE ROW LEVEL SECURITY;
ALTER TABLE api.goals DISABLE ROW LEVEL SECURITY;

-- Drop user_id columns (WARNING: This will delete all user_id data)
ALTER TABLE api.invoices DROP COLUMN IF EXISTS user_id;
ALTER TABLE api.projects DROP COLUMN IF EXISTS user_id;
ALTER TABLE api.appointments DROP COLUMN IF EXISTS user_id;
ALTER TABLE api.proposals DROP COLUMN IF EXISTS user_id;
ALTER TABLE api.contacts DROP COLUMN IF EXISTS user_id;
ALTER TABLE api.reviews DROP COLUMN IF EXISTS user_id;
ALTER TABLE api.campaigns DROP COLUMN IF EXISTS user_id;
ALTER TABLE api.tasks DROP COLUMN IF EXISTS user_id;
ALTER TABLE api.goals DROP COLUMN IF EXISTS user_id;
```
