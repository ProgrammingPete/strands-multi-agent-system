# Production Security Guide - Multi-Agent System

## ⚠️ Current Security Issue

**Problem:** The current implementation uses a **secret key** which bypasses Row Level Security (RLS). This means:
- ❌ Any user can access any other user's invoices
- ❌ No data isolation between users
- ❌ Violates principle of least privilege
- ❌ Not suitable for production

## ✅ Production-Ready Architecture

### Option 1: User-Scoped Backend (Recommended)

**Architecture:**
```
Frontend (Publishable Key)
    ↓ (sends user JWT)
Backend API (Validates JWT, extracts user_id)
    ↓ (uses user JWT for Supabase calls)
Supabase (RLS enforces user isolation)
```

**How it works:**
1. User authenticates with Supabase Auth (frontend)
2. Frontend gets user JWT token
3. Frontend sends JWT to your backend API
4. Backend validates JWT and extracts `user_id`
5. Backend makes Supabase calls **using the user's JWT** (not secret key)
6. RLS policies ensure users only see their own data

**Implementation:**

```python
# backend/auth_middleware.py
from supabase import create_client
import os

def create_user_scoped_client(user_jwt: str):
    """
    Create a Supabase client scoped to a specific user.
    This respects RLS policies.
    """
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_PUB_KEY"),  # Use pub key, not secret!
        options={
            "headers": {
                "Authorization": f"Bearer {user_jwt}"
            }
        }
    )
    return supabase

# backend/invoice_tools.py (updated)
@tool
def get_invoices(
    user_jwt: str,  # Pass JWT instead of user_id
    status: Optional[str] = None,
    client_id: Optional[str] = None,
    limit: int = 10
) -> str:
    """Fetch invoices - RLS ensures user only sees their own data."""
    supabase = create_user_scoped_client(user_jwt)
    
    # RLS policies automatically filter by user
    query = supabase.table('invoices').select('*')
    
    if status:
        query = query.eq('status', status)
    
    result = query.limit(limit).execute()
    return json.dumps(result.data)
```

**Required Database Changes:**

```sql
-- Add user_id column to invoices table
ALTER TABLE api.invoices 
ADD COLUMN user_id UUID REFERENCES auth.users(id);

-- Create index for performance
CREATE INDEX idx_invoices_user_id ON api.invoices(user_id);

-- Enable RLS
ALTER TABLE api.invoices ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only see their own invoices
CREATE POLICY "Users can view own invoices"
ON api.invoices FOR SELECT
USING (auth.uid() = user_id);

-- RLS Policy: Users can only create invoices for themselves
CREATE POLICY "Users can create own invoices"
ON api.invoices FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- RLS Policy: Users can only update their own invoices
CREATE POLICY "Users can update own invoices"
ON api.invoices FOR UPDATE
USING (auth.uid() = user_id);

-- RLS Policy: Users can only delete their own invoices
CREATE POLICY "Users can delete own invoices"
ON api.invoices FOR DELETE
USING (auth.uid() = user_id);
```

### Option 2: Service Role with Manual Filtering (Less Secure)

**Only use if you can't modify the database schema.**

```python
@tool
def get_invoices(
    user_id: str,  # MUST be validated!
    status: Optional[str] = None,
    limit: int = 10
) -> str:
    """
    Fetch invoices with manual user_id filtering.
    WARNING: Relies on application logic, not database enforcement.
    """
    supabase = get_supabase_client()  # Uses secret key
    
    # CRITICAL: Always filter by user_id
    query = supabase.table('invoices').select('*').eq('user_id', user_id)
    
    if status:
        query = query.eq('status', status)
    
    result = query.limit(limit).execute()
    return json.dumps(result.data)
```

**Problems with this approach:**
- ❌ Easy to forget filtering in one place
- ❌ No database-level enforcement
- ❌ One bug = data leak
- ❌ Harder to audit

## 🎯 Recommended Migration Path

### Phase 1: Add user_id to Schema (Do First)

```sql
-- 1. Add user_id column
ALTER TABLE api.invoices 
ADD COLUMN user_id UUID REFERENCES auth.users(id);

-- 2. Backfill existing data with a default user
-- (You'll need to decide how to handle existing invoices)
UPDATE api.invoices 
SET user_id = '00000000-0000-0000-0000-000000000000'
WHERE user_id IS NULL;

-- 3. Make it required (after backfill)
ALTER TABLE api.invoices 
ALTER COLUMN user_id SET NOT NULL;

-- 4. Add index
CREATE INDEX idx_invoices_user_id ON api.invoices(user_id);
```

### Phase 2: Enable RLS Policies

```sql
-- Enable RLS
ALTER TABLE api.invoices ENABLE ROW LEVEL SECURITY;

-- Add policies (see Option 1 above)
CREATE POLICY "Users can view own invoices"...
CREATE POLICY "Users can create own invoices"...
CREATE POLICY "Users can update own invoices"...
CREATE POLICY "Users can delete own invoices"...
```

### Phase 3: Update Backend Code

```python
# Update all tools to use user JWT instead of secret key
# See Option 1 implementation above
```

### Phase 4: Update Frontend

```typescript
// frontend/services/AgentService.ts
class AgentService {
  async sendMessage(message: string) {
    // Get user's JWT token
    const { data: { session } } = await supabase.auth.getSession()
    
    if (!session) {
      throw new Error('User not authenticated')
    }
    
    // Send JWT to backend
    const response = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`
      },
      body: JSON.stringify({ message })
    })
    
    return response
  }
}
```

### Phase 5: Remove Secret Key from Production

```bash
# .env.production
# Remove or comment out:
# SUPABASE_SERVICE_KEY=sb_secret_...

# Keep only:
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_PUB_KEY=your_pub_key_here
```

## 🔒 Security Best Practices

### 1. Never Use Secret Key for User Operations

```python
# ❌ BAD - Bypasses RLS
supabase = create_client(url, secret_key)
invoices = supabase.table('invoices').select('*').execute()

# ✅ GOOD - Respects RLS
supabase = create_client(url, pub_key, {
    "headers": {"Authorization": f"Bearer {user_jwt}"}
})
invoices = supabase.table('invoices').select('*').execute()
```

### 2. Always Validate JWTs

```python
from supabase import create_client

def validate_user_jwt(jwt: str) -> dict:
    """Validate JWT and extract user info."""
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_PUB_KEY")
    )
    
    # Verify JWT is valid
    user = supabase.auth.get_user(jwt)
    
    if not user:
        raise ValueError("Invalid JWT")
    
    return user
```

### 3. Use Secret Key Only for Admin Operations

```python
# Secret key should ONLY be used for:
# - System maintenance
# - Admin dashboards (with separate auth)
# - Background jobs (not user-initiated)
# - Testing/development

# Example: Admin endpoint (requires separate admin auth)
@app.post("/admin/invoices/bulk-update")
async def admin_bulk_update(admin_token: str):
    # Verify admin token first!
    if not verify_admin_token(admin_token):
        raise HTTPException(403, "Forbidden")
    
    # Now safe to use secret key
    supabase = create_client(url, secret_key)
    # ... admin operations
```

### 4. Implement Rate Limiting

```python
from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter

@app.post("/api/chat/stream")
@limiter.limit("10/minute")  # 10 requests per minute per user
async def chat_stream(request: Request):
    # ... handle request
```

### 5. Audit Logging

```python
import logging

logger = logging.getLogger(__name__)

def log_data_access(user_id: str, table: str, operation: str):
    """Log all data access for audit trail."""
    logger.info(
        f"Data access: user={user_id} table={table} operation={operation}",
        extra={
            "user_id": user_id,
            "table": table,
            "operation": operation,
            "timestamp": datetime.now().isoformat()
        }
    )
```

## 📊 Testing Strategy

### Development/Testing
- ✅ Use secret key for testing
- ✅ Use SYSTEM_USER_ID for batch tests
- ✅ Test with mock users

### Staging
- ✅ Use real user JWTs
- ✅ Enable RLS policies
- ✅ Test with multiple users
- ✅ Verify data isolation

### Production
- ✅ Use only user JWTs (pub key + user token)
- ✅ RLS policies enforced
- ✅ Secret key only for admin operations
- ✅ Rate limiting enabled
- ✅ Audit logging active

## 🚀 Quick Start for Production

1. **Add user_id column** (see Phase 1)
2. **Enable RLS** (see Phase 2)
3. **Update backend** to use user JWTs (see Option 1)
4. **Update frontend** to send JWTs (see Phase 4)
5. **Remove secret key** from production env (see Phase 5)
6. **Test thoroughly** with multiple users
7. **Monitor** for unauthorized access attempts

## 📝 Checklist Before Production

- [ ] user_id column added to all tables
- [ ] RLS policies created and tested
- [ ] Backend uses user JWTs (not secret key)
- [ ] Frontend sends user JWTs to backend
- [ ] Secret key removed from production env
- [ ] Rate limiting implemented
- [ ] Audit logging enabled
- [ ] Multi-user testing completed
- [ ] Security review passed
- [ ] Monitoring and alerts configured

## 🆘 If You Must Use Secret Key in Production

If you absolutely cannot implement user-scoped access right now:

1. **Add strict IP whitelisting** - Only allow backend server IPs
2. **Implement application-level filtering** - Always filter by user_id
3. **Add extensive audit logging** - Log every data access
4. **Set up alerts** - Alert on suspicious patterns
5. **Plan migration** - This is temporary, plan to migrate ASAP
6. **Regular security audits** - Review access logs weekly

**But seriously: Don't do this. Implement proper RLS instead.**

## 📚 Additional Resources

- [Supabase RLS Documentation](https://supabase.com/docs/guides/database/postgres/row-level-security)
- [Supabase Auth Documentation](https://supabase.com/docs/guides/auth)
- [API Keys Best Practices](https://supabase.com/docs/guides/api/api-keys)
- [JWT Verification](https://supabase.com/docs/guides/auth/jwts)
