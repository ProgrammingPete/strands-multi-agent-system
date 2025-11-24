# Supabase API Key Types - Complete Guide

Based on official Supabase documentation: https://supabase.com/docs/guides/api/api-keys

## Overview

Supabase provides 4 types of API keys for different use cases:

| Type | Format | Privileges | Use Case |
|------|--------|------------|----------|
| **Publishable key** | `sb_publishable_...` | Low | Frontend apps (web, mobile, desktop) |
| **Secret key** | `sb_secret_...` | Elevated | Backend servers, APIs, Edge Functions |
| **anon** (legacy) | JWT (long-lived) | Low | Same as publishable key |
| **service_role** (legacy) | JWT (long-lived) | Elevated | Same as secret key |

## Key Differences

### Publishable Key vs Secret Key

**Publishable Key (`sb_publishable_...`)**
- ✅ Safe to expose in frontend code
- ✅ Subject to Row Level Security (RLS) policies
- ✅ Used with `anon` or `authenticated` Postgres roles
- ✅ Can be committed to source control (public repos)
- ✅ Used in: Web pages, mobile apps, desktop apps, CLIs

**Secret Key (`sb_secret_...`)**
- ❌ NEVER expose publicly
- ✅ Bypasses RLS policies (full access)
- ✅ Uses `service_role` Postgres role
- ❌ Never commit to source control
- ✅ Used in: Backend servers, Edge Functions, admin panels

## When to Use Each Key

### Use Publishable Key When:
- Building frontend applications (React, Vue, Angular, etc.)
- Developing mobile apps (iOS, Android, React Native)
- Creating desktop applications
- Building CLIs or scripts that run on user machines
- Any code that will be distributed to end users

### Use Secret Key When:
- Building backend APIs
- Creating admin panels
- Writing server-side functions
- Implementing data processing pipelines
- Running periodic jobs or queue processors
- Any code that runs in a secure, developer-controlled environment

## Security Considerations

### Publishable Key Security
The publishable key provides basic protection:
- ✅ Protects against bots and scrapers
- ✅ Provides DoS protection
- ❌ Does NOT protect against:
  - Code analysis/reverse engineering
  - Network inspection
  - CSRF, XSS, phishing attacks
  - Man-in-the-middle attacks

**Protection:** Use RLS policies on all tables to control data access.

### Secret Key Security
The secret key provides full database access:
- ✅ Bypasses ALL RLS policies
- ✅ Has `BYPASSRLS` attribute in Postgres
- ❌ If leaked, attackers have full access to your data

**Best Practices:**
1. Only use on computers you fully own/control
2. Never add to source control
3. Use encrypted storage for environment variables
4. Use separate keys for each backend component
5. Delete immediately if compromised
6. Never use in browsers (even localhost!)
7. Don't pass in URLs or query params
8. Be careful with logging

## Our Issue: Wrong Key Type

### What We Had
```bash
SUPABASE_SERVICE_KEY=eyJhbGci... # This was the anon key (JWT)
```

Decoded JWT showed:
```json
{
  "role": "anon",  // ❌ Wrong! This is a publishable key
  "iss": "supabase",
  "ref": "emdlwkjdqbsbeeamgffq"
}
```

### What We Need
```bash
SUPABASE_SERVICE_KEY=sb_secret_... # Secret key format
```

This key:
- ✅ Bypasses RLS policies
- ✅ Has full database access
- ✅ Works with `api` schema
- ✅ Allows create/update/delete operations

## Migration from Legacy Keys

Supabase recommends migrating from JWT-based keys (`anon`, `service_role`) to the new format (`sb_publishable_`, `sb_secret_`):

### Why Migrate?

**Problems with Legacy JWT Keys:**
- Tight coupling between JWT secret and all keys
- Can't rotate independently without downtime
- Can't roll back problematic rotations
- Mobile apps can't update keys quickly (app store delays)
- 10-year expiry gives attackers more time
- Large, hard to parse, insecure to log

**Benefits of New Keys:**
- Independent rotation (no downtime)
- Easier to manage and revoke
- Better security practices
- Smaller, easier to handle
- Can create multiple keys for different components

### How to Get Secret Key

1. Go to Supabase Dashboard
2. Navigate to: **Settings** → **API** → **Secret Keys**
3. Click "Create new secret key"
4. Copy the key (starts with `sb_secret_...`)
5. Update your `.env` file:
   ```bash
   SUPABASE_SERVICE_KEY=sb_secret_your_key_here
   ```

## Schema Access Issue

Even with the correct secret key, you may encounter:
```
Error: permission denied for schema api
```

This means the secret key doesn't have permission to access the `api` schema.

### Solution

Run this SQL in Supabase:
```sql
GRANT USAGE ON SCHEMA api TO authenticated, anon, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA api TO authenticated, anon, service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA api TO authenticated, anon, service_role;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA api TO authenticated, anon, service_role;
```

## Verification

Use our verification script to check your key:
```bash
uv run python tests/verify_supabase_key.py
```

Expected output with correct secret key:
```
✅ CORRECT: Using Supabase Secret API Key
   This is the new recommended format for server-side access.
   Secret keys bypass RLS policies and have full access.
```

## Summary

| Aspect | Publishable Key | Secret Key |
|--------|----------------|------------|
| **Format** | `sb_publishable_...` | `sb_secret_...` |
| **Exposure** | Safe to expose | NEVER expose |
| **RLS** | Subject to RLS | Bypasses RLS |
| **Use in** | Frontend | Backend only |
| **Postgres Role** | `anon`/`authenticated` | `service_role` |
| **Source Control** | ✅ Can commit | ❌ Never commit |
| **Browser** | ✅ Safe | ❌ Blocked |

## References

- [Supabase API Keys Documentation](https://supabase.com/docs/guides/api/api-keys)
- [Row Level Security Guide](https://supabase.com/docs/guides/database/postgres/row-level-security)
- [JWT Signing Keys](https://supabase.com/docs/guides/auth/signing-keys)
