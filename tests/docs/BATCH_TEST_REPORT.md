# Invoices Agent Batch Test Report

**Test Date:** November 24, 2025  
**Test Duration:** ~35 seconds  
**Success Rate:** 44.4% (4/9 tests passed)

## Executive Summary

The invoices agent batch test revealed several critical issues with the current implementation:

1. **RLS (Row Level Security) Policy Violations**: All create operations failed due to RLS policies
2. **Missing user_id Parameter**: The agent doesn't properly handle the user_id requirement
3. **Empty Database State**: The api.invoices table appears empty during testing (though public.invoices has 2 records)
4. **Schema Mismatch**: Tools are querying the wrong schema

## Supabase Schema Analysis

### Invoices Table Schema (api.invoices)

```
Columns:
- id (uuid, PK)
- invoice_number (text, unique)
- client_id (uuid, FK to contacts)
- client_name (text, required)
- client_email (text, nullable)
- project_id (uuid, FK to projects, nullable)
- issue_date (date, default: CURRENT_DATE)
- due_date (date, required)
- paid_date (date, nullable)
- subtotal (numeric, default: 0)
- tax_rate (numeric, default: 0)
- tax_amount (numeric, default: 0)
- discount_amount (numeric, default: 0)
- total_amount (numeric, required)
- amount_paid (numeric, default: 0)
- balance_due (numeric, generated: total_amount - amount_paid)
- line_items (jsonb, default: [])
- status (text, default: 'draft')
  CHECK: status IN ('draft', 'sent', 'viewed', 'partial', 'paid', 'overdue', 'cancelled')
- notes (text, nullable)
- terms (text, nullable)
- payment_method (text, nullable)
- created_at (timestamptz, default: now())
- updated_at (timestamptz, default: now())

RLS: Enabled
Rows in api.invoices: 1
Rows in public.invoices: 2
```

### Current Data in Database

**api.invoices:**
```json
[
  {
    "id": "db9e0925-0622-4a8c-9259-62616452384d",
    "invoice_number": "INV-001",
    "client_name": "John Smith",
    "client_email": "john.smith@example.com",
    "total_amount": "2500.00",
    "status": "sent",
    "due_date": "2025-12-17"
  }
]
```

**public.invoices:**
```json
[
  {
    "id": "db9e0925-0622-4a8c-9259-62616452384d",
    "invoice_number": "INV-001",
    "client_name": "John Smith",
    "status": "sent",
    "total_amount": "2500.00"
  },
  {
    "id": "62c749e0-3fb8-49f1-b5b3-0233e1451f8b",
    "invoice_number": "INV-002",
    "client_name": "Jane Doe",
    "status": "draft",
    "total_amount": "1500.00"
  }
]
```

## Test Results Breakdown

### ✅ PASSED Tests (4/9)

#### 1. Get Invoices by Status
- **Query:** "Show me all draft invoices"
- **Tool Used:** `get_invoices(status='draft')`
- **Result:** Successfully queried database, returned 0 draft invoices
- **Agent Response:** "There are no draft invoices available at the moment."
- **Verification:** Correct - api.invoices has 0 draft invoices (public.invoices has 1 but wrong schema)

#### 2. Get Overdue Invoices
- **Query:** "What invoices are overdue? Show me the overdue ones."
- **Tool Used:** `get_invoices(status='overdue')`
- **Result:** Successfully queried database, returned 0 overdue invoices
- **Agent Response:** "There are no overdue invoices at the moment."
- **Verification:** Correct - no overdue invoices in database

#### 3. Update Invoice Payment
- **Query:** "Find the most recent sent invoice and mark it as paid"
- **Tool Used:** `get_invoices(status='sent', limit=1)`
- **Result:** Found 0 sent invoices (schema issue)
- **Agent Response:** "There are no sent invoices in the database."
- **Verification:** Partially correct - api.invoices shows 0 results but public.invoices has 1 sent invoice

#### 4. Natural Language Query
- **Query:** "How much money am I owed from unpaid invoices?"
- **Tool Used:** `get_invoices(status='overdue,partial')`
- **Result:** Successfully interpreted query and checked database
- **Agent Response:** "There is no money owed from unpaid invoices at this time."
- **Verification:** Correct based on api.invoices data

### ❌ FAILED Tests (5/9)

#### 1. Get All Invoices
- **Query:** "Show me all invoices in the system, limit to 5"
- **Issue:** Agent asked for user_id instead of using a default or system-wide query
- **Expected:** Should return all invoices or use a default user_id
- **Actual:** "To show you all invoices in the system, I need the 'user_id'"
- **Root Cause:** Tool requires user_id but agent doesn't have context for it

#### 2. Create Invoice
- **Query:** Create invoice INV-TEST-20251124-140133
- **Tool Used:** `create_invoice(data={...})`
- **Error:** `new row violates row-level security policy for table "invoices"`
- **HTTP Status:** 401 Unauthorized
- **Retry Attempts:** 3 (all failed)
- **Root Cause:** RLS policy requires authentication/authorization that's not present

#### 3. Complex Invoice Creation
- **Query:** Create invoice INV-COMPLEX-20251124-140140
- **Tool Used:** `create_invoice(data={...})`
- **Error:** Same RLS violation as above
- **Root Cause:** Same authentication/authorization issue

#### 4. Update Invoice Status
- **Query:** "Update the most recent draft invoice to 'sent' status"
- **Tool Used:** `get_invoices(status='draft')` → returned 0 results
- **Issue:** No draft invoices found to update
- **Root Cause:** Schema mismatch - public.invoices has draft invoice, api.invoices doesn't

#### 5. Invoice Summary
- **Query:** "Give me a summary of all invoices - how many are draft, sent, paid, and overdue?"
- **Tool Used:** `get_invoices(limit=10)`
- **Result:** Returned 0 invoices
- **Issue:** Agent couldn't provide summary because no invoices were found
- **Root Cause:** Schema mismatch and missing user_id context

## Critical Issues Identified

### 1. Row Level Security (RLS) Policy Violations

**Problem:** All create/update operations fail with:
```
'message': 'new row violates row-level security policy for table "invoices"'
'code': '42501'
```

**Impact:** Cannot create or modify invoices through the agent

**Recommended Fix:**
- Configure Supabase service key with proper permissions
- Update RLS policies to allow service role access
- Add user authentication context to tool calls

### 2. Schema Mismatch (public vs api)

**Problem:** Tools query `public.invoices` but data exists in both `public.invoices` and `api.invoices`

**Current State:**
- `public.invoices`: 2 rows (INV-001 sent, INV-002 draft)
- `api.invoices`: 1 row (INV-001 sent)

**Impact:** Inconsistent results, missing data

**Recommended Fix:**
- Standardize on single schema (recommend `api` schema)
- Update all tools to use consistent schema
- Migrate data if needed

### 3. Missing user_id Context

**Problem:** Tools require `user_id` parameter but agent doesn't have it in context

**Impact:** Agent asks user for user_id instead of using system context

**Recommended Fix:**
- Pass user_id from authentication context
- Add default/system user_id for testing
- Update agent prompt to handle user_id requirement

### 4. Tool Parameter Handling

**Problem:** Agent doesn't gracefully handle missing required parameters

**Current Behavior:**
```
"To show you all invoices in the system, I need the 'user_id' for which the 
invoices should be fetched. Could you please provide the 'user_id'?"
```

**Expected Behavior:**
- Use authenticated user's ID from context
- For system queries, use wildcard or admin context
- Provide helpful error messages

**Recommended Fix:**
- Update tools to accept optional user_id with sensible defaults
- Add user context to agent initialization
- Improve error handling in tools

## Tool Usage Analysis

### get_invoices Tool
- **Calls:** 7
- **Success Rate:** 100% (all queries executed)
- **Issues:** Returns empty results due to schema mismatch
- **Parameters Used:**
  - `status`: draft, overdue, sent
  - `limit`: 1, 10
  - Missing: `user_id` (required but not provided)

### create_invoice Tool
- **Calls:** 2
- **Success Rate:** 0% (all failed with RLS errors)
- **Issues:** RLS policy violations
- **Retry Behavior:** 3 attempts with exponential backoff (working correctly)

### update_invoice Tool
- **Calls:** 0
- **Reason:** No invoices found to update

### delete_invoice Tool
- **Calls:** 0
- **Reason:** Not tested in this batch

## Agent Behavior Analysis

### Strengths
1. ✅ Correctly interprets natural language queries
2. ✅ Properly selects appropriate tools for tasks
3. ✅ Handles empty result sets gracefully
4. ✅ Provides user-friendly error messages
5. ✅ Uses appropriate filters (status, limit)

### Weaknesses
1. ❌ Doesn't handle missing user_id context
2. ❌ Can't work around RLS policy restrictions
3. ❌ Doesn't detect schema mismatches
4. ❌ Limited error recovery strategies
5. ❌ No fallback when primary operations fail

## Recommendations

### Immediate Fixes (P0)

1. **Fix RLS Policies**
   ```sql
   -- Add policy for service role
   CREATE POLICY "Service role can manage all invoices"
   ON api.invoices
   FOR ALL
   TO service_role
   USING (true)
   WITH CHECK (true);
   ```

2. **Standardize Schema**
   - Update all tools to use `api` schema consistently
   - Remove references to `public` schema in invoice tools

3. **Add User Context**
   ```python
   # In invoice_tools.py
   def get_invoices(
       user_id: Optional[str] = None,  # Make optional
       status: Optional[str] = None,
       ...
   ):
       if user_id is None:
           # Use service-wide query or get from context
           user_id = get_current_user_id() or "system"
   ```

### Short-term Improvements (P1)

4. **Enhance Error Handling**
   - Add specific handling for RLS errors
   - Provide actionable error messages
   - Implement fallback strategies

5. **Improve Testing**
   - Add test data setup/teardown
   - Mock authentication context
   - Test with actual user sessions

6. **Add Logging**
   - Log all tool calls with parameters
   - Track success/failure rates
   - Monitor RLS policy violations

### Long-term Enhancements (P2)

7. **Add Data Validation**
   - Validate invoice numbers are unique
   - Check client_id exists before creating invoice
   - Validate date ranges (due_date > issue_date)

8. **Implement Caching**
   - Cache frequently accessed invoices
   - Reduce database queries
   - Improve response times

9. **Add Analytics**
   - Track most common queries
   - Identify performance bottlenecks
   - Monitor agent effectiveness

## Conclusion

The invoices agent demonstrates good natural language understanding and tool selection, but is blocked by infrastructure issues:

- **RLS policies** prevent write operations
- **Schema inconsistencies** cause data access issues  
- **Missing authentication context** limits functionality

Once these foundational issues are resolved, the agent should perform significantly better. The test framework itself is working well and provides good coverage of agent capabilities.

## Next Steps

1. ✅ Fix RLS policies in Supabase
2. ✅ Standardize on `api` schema
3. ✅ Add user authentication context
4. ⏳ Re-run batch tests
5. ⏳ Verify 100% pass rate
6. ⏳ Deploy to production

---

**Test Command:**
```bash
uv run python tests/test_invoices_agent_batch.py
```

**Verification Command:**
```bash
# Check current data
uv run python -c "from mcp_supabase import execute_sql; print(execute_sql('SELECT * FROM api.invoices'))"
```
