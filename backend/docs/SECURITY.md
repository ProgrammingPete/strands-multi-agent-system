# Production Security Implementation

This document describes the security architecture for the Canvalo multi-agent system, including Row Level Security (RLS), JWT authentication, and user data isolation.

## Overview

The system implements a production-ready security model that ensures:
- Users can only access their own data
- All database operations respect RLS policies
- JWT-based authentication for API requests
- Proper separation between development and production environments

## Architecture

### Current State (Development)
```
Frontend (No Auth)
    ↓
Backend API (Secret Key)
    ↓
Supabase (RLS Bypassed)
    ↓
PostgreSQL Database
```

### Target State (Production)
```
Frontend (Supabase Auth)
    ↓ (User JWT)
Backend API (JWT Validation)
    ↓ (User-Scoped Client)
Supabase (RLS Enforced)
    ↓
PostgreSQL Database (RLS Policies)
```

## Database Security

### Row Level Security (RLS)

All api schema tables have RLS enabled with policies for:
- **SELECT**: Users can only view their own records
- **INSERT**: Users can only create records with their own user_id
- **UPDATE**: Users can only modify their own records
- **DELETE**: Users can only delete their own records

### Tables with RLS

| Table | user_id Column | RLS Enabled | Policies |
|-------|---------------|-------------|----------|
| api.invoices | ✅ | ✅ | SELECT, INSERT, UPDATE, DELETE |
| api.projects | ✅ | ✅ | SELECT, INSERT, UPDATE, DELETE |
| api.appointments | ✅ | ✅ | SELECT, INSERT, UPDATE, DELETE |
| api.proposals | ✅ | ✅ | SELECT, INSERT, UPDATE, DELETE |
| api.contacts | ✅ | ✅ | SELECT, INSERT, UPDATE, DELETE |
| api.reviews | ✅ | ✅ | SELECT, INSERT, UPDATE, DELETE |
| api.campaigns | ✅ | ✅ | SELECT, INSERT, UPDATE, DELETE |
| api.tasks | ✅ | ✅ | SELECT, INSERT, UPDATE, DELETE |
| api.goals | ✅ | ✅ | SELECT, INSERT, UPDATE, DELETE |

### Migration Script

The database schema changes are defined in `migrations/add_user_id_and_rls.sql`. See [migrations/README.md](../../migrations/README.md) for execution instructions.

## Authentication

### JWT Validation

All API requests must include a valid JWT token in the Authorization header:
```
Authorization: Bearer <jwt_token>
```

The backend validates JWTs using Supabase's `auth.get_user()` method, which:
- Validates the JWT signature
- Checks token expiration
- Verifies the token was issued by the Supabase project
- Returns the user object if valid

### Auth Middleware (`backend/auth_middleware.py`)

The authentication middleware provides:

```python
from backend.auth_middleware import validate_jwt, extract_user_id, AuthenticationError

# Validate JWT and get user_id
try:
    user_id = validate_jwt(jwt_token)
except AuthenticationError as e:
    # Handle authentication failure
    print(f"Error: {e.code} - {e.user_message}")
```

**Error Codes:**
| Code | Description | User Message |
|------|-------------|--------------|
| `INVALID_TOKEN` | Token signature invalid | "Your session is invalid. Please log in again." |
| `EXPIRED_TOKEN` | Token has expired | "Your session has expired. Please log in again." |
| `MISSING_TOKEN` | No token provided | "Authentication required. Please log in." |
| `MALFORMED_TOKEN` | Token format invalid | "Invalid authentication format. Please log in again." |
| `CONFIGURATION_ERROR` | Server misconfigured | "Server configuration error. Please contact support." |

### User-Scoped Clients

When processing authenticated requests, the backend creates user-scoped Supabase clients that:
- Use the anon key (not the secret key)
- Include the user's JWT in the Authorization header
- Respect all RLS policies

```python
from utils.supabase_client import get_supabase_client

# Create user-scoped client
wrapper = get_supabase_client()
user_client = wrapper.create_user_scoped_client(user_jwt)

# All queries now respect RLS
data = user_client.schema("api").table("invoices").select("*").execute()
```

### Key Configuration Verification

On startup, verify key configuration:

```python
config = wrapper.verify_key_configuration()
# Returns: {
#   "key_type": "service_key" or "anon_key",
#   "has_anon_key": True/False,
#   "is_valid": True/False,
#   "warnings": [...],
#   "environment": "development" or "production"
# }
```

## Environment Configuration

### Development (.env)
```bash
SUPABASE_URL=https://project.supabase.co
SUPABASE_ANON_KEY=eyJhbGci...        # For user operations
SUPABASE_SERVICE_KEY=sb_secret_...   # For system operations (dev only)
ENVIRONMENT=development
SYSTEM_USER_ID=00000000-0000-0000-0000-000000000000
```

### Production (.env.production)
```bash
SUPABASE_URL=https://project.supabase.co
SUPABASE_ANON_KEY=eyJhbGci...        # For user operations
# SUPABASE_SERVICE_KEY removed in production
ENVIRONMENT=production
```

## Security Best Practices

1. **Never expose the secret key** in production environments
2. **Always validate JWTs** before processing requests
3. **Use user-scoped clients** for all user data operations
4. **Rely on RLS policies** for data filtering (don't filter manually)
5. **Log security events** for audit and monitoring

## Implementation Status

### Completed ✅
- [x] Database schema with user_id columns
- [x] RLS policies for all tables
- [x] Schema permissions for Postgres roles
- [x] Backend JWT validation middleware (`backend/auth_middleware.py`)
- [x] User-scoped Supabase client factory (`utils/supabase_client.py`)
- [x] Configuration settings for anon key and environment (`backend/config.py`)

### In Progress 🔄
- [ ] Backend API JWT integration (main.py endpoints)
- [ ] Agent tools refactoring (user_id parameter)
- [ ] Frontend JWT integration

### Planned 📋
- [ ] Rate limiting
- [ ] Audit logging
- [ ] Security monitoring and alerts

## Related Documentation

- [Migration README](../../migrations/README.md) - Database migration instructions
- [API Reference](API_REFERENCE.md) - API endpoints and authentication
- [Production Security Spec](../../.kiro/specs/production-security/) - Full specification
