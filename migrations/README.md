# Database Migrations

This directory contains SQL migration scripts for the Canvalo multi-agent system, implementing production-ready security with Row-Level Security (RLS) and user data isolation.

## Overview

The migration system ensures that the Supabase PostgreSQL database is properly configured for multi-user access with strict security policies. All business entity tables are migrated to support user-scoped operations that integrate seamlessly with the multi-agent system.

## Migration Scripts

### `add_user_id_and_rls.sql` - Production Security Migration

This comprehensive migration implements user data isolation and Row-Level Security across all 9 business entity tables in the api schema.

**What it implements:**

1. **User ID Columns**: Adds `user_id UUID` columns to all 9 business entity tables:
   - `api.invoices` - Invoice management with user isolation
   - `api.projects` - Project tracking per user
   - `api.appointments` - User-specific scheduling
   - `api.proposals` - Estimates and quotes per user
   - `api.contacts` - CRM with user-scoped contacts
   - `api.reviews` - Customer feedback per user
   - `api.campaigns` - Marketing campaigns per user
   - `api.tasks` - Task management with user isolation
   - `api.goals` - Business objectives per user

2. **Foreign Key Constraints**: Creates references to `auth.users(id)` for data integrity

3. **Performance Indexes**: Creates indexes on all `user_id` columns for optimal query performance

4. **Row-Level Security (RLS)**: Enables RLS on all tables with comprehensive policies:
   - **SELECT Policy**: Users can only view their own records (`auth.uid() = user_id`)
   - **INSERT Policy**: Users can only create records with their own user_id
   - **UPDATE Policy**: Users can only modify their own records
   - **DELETE Policy**: Users can only delete their own records

5. **Schema Permissions**: Grants appropriate permissions to PostgreSQL roles:
   - `authenticated` role: Full CRUD access with RLS enforcement
   - `anon` role: Limited access for public operations
   - `service_role` role: Administrative access (bypasses RLS)

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
