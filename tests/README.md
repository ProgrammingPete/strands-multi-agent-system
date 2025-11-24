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
```

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
- 🔄 Additional agents (to be added as implemented)

## Requirements

Tests require:
- Python 3.13+
- All project dependencies installed
- Environment variables configured (`.env` file)
- Supabase credentials (for integration tests)

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
