# Tests Directory

This directory contains all test modules for the Canvalo multi-agent system.

## Test Modules

### `test_foundation.py`
Tests the Phase 1 foundation implementation:
- Supervisor agent initialization
- Supabase client connection
- CRUD tool generators
- Retry logic

### `test_invoices_agent.py`
Tests the Invoices Agent implementation:
- Agent imports and structure
- Invoice tools (get, create, update, delete)
- Supervisor integration

### `test_invoices_agent_batch.py`
Comprehensive batch integration tests for the Invoices Agent:
- End-to-end invoice creation (simple and complex)
- Invoice retrieval (all, by status, overdue)
- Invoice updates (status changes, payment recording)
- Invoice summaries and analytics
- Natural language query handling
- Real Supabase integration testing

### `test_e2e.py`
End-to-end tests for the complete multi-agent chat system:
- **Server Health**: Health check and root endpoint tests
- **Basic Chat Flow**: Message sending, streaming responses, message persistence
- **Agent Routing**: Invoice queries, unimplemented domain handling
- **Multi-Agent Coordination**: Ambiguous query handling
- **Voice Mode**: Transcript processing, TTS response handling
- **Error Scenarios**: Invalid IDs, empty messages, missing fields, non-existent resources
- **Conversation Management**: CRUD operations for conversations

Requirements covered: 12.1-12.12, 14.1-14.5, 15.1-15.2, 16.1-16.5, 17.1-17.4

### `test_rls_properties.py`
Property-based tests for Row Level Security (RLS) policy enforcement:
- **RLS SELECT Enforcement**: Verifies users can only see their own data
- **Multi-User Data Isolation**: Ensures complete data isolation between users
- **RLS CRUD Completeness**: Validates all CRUD operations have proper RLS policies

Requirements covered: 2.3, 2.4, 9.1, 9.2, 9.4

### `conftest.py`
Pytest configuration and shared fixtures:
- **System User Fixtures**: `system_user_id`, `test_environment`, `is_development_mode`
- **Supabase Client Fixtures**: `supabase_client`, `user_scoped_client`
- **Test Data Fixtures**: `test_invoice_data`, `test_project_data`, `test_contact_data`
- **Data Cleanup Fixtures**: `test_data_tracker`, `cleanup_test_data`
- **Agent Tool Fixtures**: `invoice_tools_with_user`

Requirements covered: 12.1, 12.2, 12.3, 12.5

### `test_cleanup.py`
Test data cleanup utilities:
- **TestDataCleanupManager**: Class for tracking and cleaning up test data
- **test_data_context**: Context manager for automatic cleanup
- **cleanup_test_invoices_by_prefix**: Utility for cleaning up test invoices
- **cleanup_all_test_data_for_user**: Utility for cleaning up all user data

Requirements covered: 12.5

## Running Tests

### Run All Tests
```bash
# From project root
python tests/run_all_tests.py

# Or from tests directory
python run_all_tests.py
```

### Run Specific Test
```bash
# Run foundation tests only
python tests/run_all_tests.py --test foundation

# Run invoices tests only
python tests/run_all_tests.py --test invoices

# Run e2e tests (requires server running)
uv run pytest tests/test_e2e.py -v
```

### Run E2E Tests
The e2e tests require the FastAPI server to be running:
```bash
# Terminal 1: Start the server
uv run python -m backend.main

# Terminal 2: Run e2e tests
uv run pytest tests/test_e2e.py -v --tb=short
```

The e2e tests authenticate with Supabase using the same test credentials as the frontend (`TEST_USER_EMAIL` and `TEST_USER_PASSWORD` from `.env`).

### Verbose Output
```bash
# Run with detailed output
python tests/run_all_tests.py --verbose

# Combine with specific test
python tests/run_all_tests.py -v -t foundation
```

### Run Individual Test Module
```bash
# Run a single test module directly
python tests/test_foundation.py
python tests/test_invoices_agent.py
```

## Test Structure

Each test module should:
1. Have a filename starting with `test_`
2. Contain a `main()` function that returns 0 for success, 1 for failure
3. Print clear pass/fail indicators (✅/❌)
4. Include a summary of test results

## Adding New Tests

To add a new test module:

1. Create a new file: `tests/test_<feature>.py`
2. Implement test functions
3. Create a `main()` function that runs all tests
4. Return 0 for success, 1 for failure

Example structure:
```python
#!/usr/bin/env python3
"""Test module for <feature>."""

import sys

def test_something():
    """Test a specific feature."""
    try:
        # Test code here
        print("✅ Test passed")
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("FEATURE TESTS")
    print("=" * 60)
    
    results = [
        ("Test Name", test_something()),
    ]
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
```

## Continuous Integration

The test suite can be integrated into CI/CD pipelines:

```bash
# Exit code 0 = all tests passed
# Exit code 1 = one or more tests failed
python tests/run_all_tests.py
```

## Test Coverage

Current test coverage:
- ✅ Phase 1 Foundation (supervisor, Supabase, CRUD tools)
- ✅ Invoices Agent (agent, tools, integration)
- ✅ End-to-End Tests (chat flow, streaming, routing, errors, conversations)
- ✅ RLS Property Tests (data isolation, CRUD completeness)
- ✅ Test Infrastructure (fixtures, cleanup, SYSTEM_USER_ID support)
- 🔄 Additional agents (to be added as implemented)
- 🔄 Rate Limiting Tests (to be implemented)
- 🔄 Audit Logging Tests (to be implemented)

## Requirements

Tests require:
- Python 3.13+
- All project dependencies installed
- Environment variables configured (`.env` file)
- Supabase credentials (for integration tests)

## Test User Configuration

All tests use the `SYSTEM_USER_ID` environment variable to associate test data with a known user account. This ensures:
- Test data is properly isolated
- RLS policies can be tested correctly
- Test cleanup can target specific user data

### Environment Variables for Testing

```bash
# Required for test data operations
SYSTEM_USER_ID=your-test-user-uuid

# Optional: For JWT-based testing
TEST_USER_JWT=your-test-jwt-token
TEST_USER_EMAIL=test@example.com
TEST_USER_PASSWORD=your-test-password
```

### Using Test Fixtures

The `conftest.py` provides fixtures that automatically use `SYSTEM_USER_ID`:

```python
def test_create_invoice(system_user_id, test_invoice_data, cleanup_test_data):
    """Test creating an invoice with automatic cleanup."""
    # test_invoice_data already has user_id set to system_user_id
    result = create_invoice(user_id=system_user_id, data=json.dumps(test_invoice_data))
    
    # Track for cleanup
    result_data = json.loads(result)
    if result_data.get("success"):
        cleanup_test_data.track('invoices', result_data['data']['id'])
    
    assert result_data.get("success")
```

### Test Data Cleanup

Use the cleanup utilities to manage test data:

```python
from tests.test_cleanup import test_data_context, cleanup_test_invoices_by_prefix

# Automatic cleanup with context manager
with test_data_context() as tracker:
    # Create test data
    invoice_id = create_test_invoice()
    tracker.track('invoices', invoice_id)
    
    # Run tests...
# Cleanup happens automatically

# Manual cleanup by prefix
cleanup_test_invoices_by_prefix("INV-TEST-")
```

### Command-Line Cleanup

```bash
# Clean up test invoices by prefix
uv run python tests/test_cleanup.py --prefix "INV-TEST-"

# Clean up ALL data for a specific user (use with caution)
uv run python tests/test_cleanup.py --user-id "your-user-id" --all
```

## Troubleshooting

### Import Errors
If you encounter import errors, ensure you're running tests from the project root:
```bash
cd strands-multi-agent-system
python tests/run_all_tests.py
```

### Supabase Connection Errors
Some tests may show warnings if Supabase is not configured. This is expected and won't fail the tests unless actual functionality is broken.

### Module Not Found
Ensure all dependencies are installed:
```bash
uv sync
# or
pip install -r requirements.txt
```
