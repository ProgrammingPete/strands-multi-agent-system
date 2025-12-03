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
# ADMIN_API_KEY=your-secure-key      # Optional in development
```

### Production (.env.production)
```bash
SUPABASE_URL=https://project.supabase.co
SUPABASE_ANON_KEY=eyJhbGci...        # For user operations
# SUPABASE_SERVICE_KEY removed in production - SECURITY REQUIREMENT
ENVIRONMENT=production
ADMIN_API_KEY=your-secure-admin-key  # Required for admin operations
```

See `.env.production.example` for a complete production configuration template.

### Configuration Validation

The backend validates configuration on startup:

```python
from backend.config import settings, validate_startup_configuration, ConfigurationError

# Called automatically during app startup
try:
    validate_startup_configuration()
except ConfigurationError as e:
    # In production, this will prevent the app from starting
    print(f"Configuration errors: {e.errors}")
```

**Production Validation Rules:**
- `SUPABASE_SERVICE_KEY` must NOT be set (security risk - bypasses RLS)
- `SUPABASE_ANON_KEY` must be set (required for user authentication)
- `SUPABASE_URL` must be set

## Admin Operations

### Admin Authentication (`backend/admin_auth.py`)

Admin operations that require the service key (which bypasses RLS) must be authenticated with an admin API key:

```python
from backend.admin_auth import validate_admin_operation, AdminAuthenticationError

try:
    # Validate admin credentials before privileged operation
    validate_admin_operation(
        api_key="admin-api-key",
        operation="bulk_data_migration",
        resource="invoices"
    )
except AdminAuthenticationError as e:
    print(f"Admin auth failed: {e.code} - {e.message}")
```

### Getting Admin Client

To get a Supabase client with service key for admin operations:

```python
from utils.supabase_client import get_supabase_client

wrapper = get_supabase_client()
admin_client = wrapper.get_admin_client(
    admin_api_key="your-admin-key",
    operation="data_migration",
    resource="invoices"
)
# admin_client bypasses RLS - use with caution
```

### Admin Error Codes

| Code | Description |
|------|-------------|
| `ADMIN_NOT_CONFIGURED` | ADMIN_API_KEY not set in production |
| `ADMIN_KEY_REQUIRED` | No API key provided for admin operation |
| `INVALID_ADMIN_KEY` | Provided API key doesn't match |

### Generating Admin API Key

Generate a secure admin API key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Admin Operation Logging

All admin operations are logged for audit purposes:
- Operation attempted (with timestamp)
- Operation authorized/denied
- Resource being accessed

Example log output:
```
INFO - Admin operation attempted: operation=bulk_migration, resource=invoices, timestamp=2024-12-02T10:30:00
WARNING - Admin client created for operation: bulk_migration. RLS policies will be bypassed.
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
- [x] Backend API JWT integration (`backend/main.py`)
- [x] Agent tools refactoring with user_id parameter
- [x] Frontend JWT integration (`AgentService.ts`)
- [x] Production environment configuration validation
- [x] Admin operation authentication (`backend/admin_auth.py`)
- [x] Multi-user data isolation testing

### In Progress 🔄
- [ ] Rate limiting implementation
- [ ] Audit logging implementation
- [ ] Test infrastructure updates

### Planned 📋
- [ ] Security monitoring and alerts
- [ ] Brute-force attack detection

## Related Documentation

- [Migration README](../../migrations/README.md) - Database migration instructions
- [API Reference](API_REFERENCE.md) - API endpoints and authentication
- [Production Security Spec](../../.kiro/specs/production-security/) - Full specification
