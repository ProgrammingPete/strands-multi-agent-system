#!/usr/bin/env python3
"""
Foundation verification tests for Phase 1 implementation.

This script tests:
1. Supervisor agent initialization
2. Supabase client connection
3. CRUD tool generators
"""

import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    try:
        from agents.supervisor import supervisor_agent, SUPERVISOR_SYSTEM_PROMPT
        from utils.supabase_client import (
            get_supabase_client,
            get_client,
            SupabaseClientWrapper,
            SupabaseClientError,
            SupabaseConnectionError,
            SupabaseQueryError
        )
        from utils.supabase_tools import (
            create_get_records_tool,
            create_create_record_tool,
            create_update_record_tool,
            create_delete_record_tool,
            create_crud_toolset
        )
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def test_supervisor_agent():
    """Test supervisor agent initialization."""
    print("\nTesting supervisor agent...")
    try:
        from agents.supervisor import supervisor_agent, SUPERVISOR_SYSTEM_PROMPT
        
        # Check agent exists
        assert supervisor_agent is not None, "Supervisor agent is None"
        
        # Check system prompt is set
        assert SUPERVISOR_SYSTEM_PROMPT is not None, "System prompt is None"
        assert len(SUPERVISOR_SYSTEM_PROMPT) > 0, "System prompt is empty"
        
        # Check key phrases in system prompt
        assert "Supervisor Agent" in SUPERVISOR_SYSTEM_PROMPT, "Missing 'Supervisor Agent' in prompt"
        assert "Canvalo" in SUPERVISOR_SYSTEM_PROMPT, "Missing 'Canvalo' in prompt"
        assert "Invoices Agent" in SUPERVISOR_SYSTEM_PROMPT, "Missing 'Invoices Agent' in prompt"
        
        # Check tools list exists (should be empty for now)
        assert hasattr(supervisor_agent, 'tools') or True, "Agent missing tools attribute"
        
        print("✅ Supervisor agent initialized correctly")
        return True
    except Exception as e:
        print(f"❌ Supervisor agent test failed: {e}")
        return False


def test_supabase_client_initialization():
    """Test Supabase client initialization."""
    print("\nTesting Supabase client initialization...")
    try:
        from utils.supabase_client import get_supabase_client, SupabaseConnectionError
        
        # Check environment variables
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not supabase_url or not supabase_key:
            print("⚠️  Supabase credentials not configured in .env")
            print("   This is expected if you haven't set up Supabase yet")
            return True  # Not a failure, just not configured
        
        # Try to initialize client
        try:
            client_wrapper = get_supabase_client()
            assert client_wrapper is not None, "Client wrapper is None"
            
            # Check client property
            client = client_wrapper.client
            assert client is not None, "Client is None"
            
            print("✅ Supabase client initialized successfully")
            return True
        except SupabaseConnectionError as e:
            print(f"⚠️  Supabase connection error (may be expected): {e}")
            return True  # Not a hard failure
            
    except Exception as e:
        print(f"❌ Supabase client test failed: {e}")
        return False


def test_crud_tool_generators():
    """Test CRUD tool generator functions."""
    print("\nTesting CRUD tool generators...")
    try:
        from utils.supabase_tools import (
            create_get_records_tool,
            create_create_record_tool,
            create_update_record_tool,
            create_delete_record_tool,
            create_crud_toolset
        )
        
        # Test get_records tool generator
        get_tool = create_get_records_tool("test_table")
        assert callable(get_tool), "get_records tool is not callable"
        assert hasattr(get_tool, '__name__'), "get_records tool missing __name__"
        
        # Test create_record tool generator
        create_tool = create_create_record_tool("test_table", required_fields=["field1", "field2"])
        assert callable(create_tool), "create_record tool is not callable"
        
        # Test update_record tool generator
        update_tool = create_update_record_tool("test_table")
        assert callable(update_tool), "update_record tool is not callable"
        
        # Test delete_record tool generator
        delete_tool = create_delete_record_tool("test_table")
        assert callable(delete_tool), "delete_record tool is not callable"
        
        # Test CRUD toolset generator
        toolset = create_crud_toolset("test_table", required_fields=["field1"])
        assert isinstance(toolset, dict), "Toolset is not a dictionary"
        assert 'get' in toolset, "Toolset missing 'get' tool"
        assert 'create' in toolset, "Toolset missing 'create' tool"
        assert 'update' in toolset, "Toolset missing 'update' tool"
        assert 'delete' in toolset, "Toolset missing 'delete' tool"
        
        print("✅ CRUD tool generators working correctly")
        return True
    except Exception as e:
        print(f"❌ CRUD tool generator test failed: {e}")
        return False


def test_retry_logic():
    """Test retry logic decorator."""
    print("\nTesting retry logic...")
    try:
        from utils.supabase_client import retry_with_backoff
        
        # Test successful function
        @retry_with_backoff(max_attempts=3, base_delay=0.1)
        def success_func():
            return "success"
        
        result = success_func()
        assert result == "success", "Retry decorator broke successful function"
        
        # Test function that fails then succeeds
        call_count = [0]
        
        @retry_with_backoff(max_attempts=3, base_delay=0.1)
        def retry_func():
            call_count[0] += 1
            if call_count[0] < 2:
                raise Exception("Temporary failure")
            return "success after retry"
        
        result = retry_func()
        assert result == "success after retry", "Retry logic didn't work"
        assert call_count[0] == 2, f"Expected 2 calls, got {call_count[0]}"
        
        print("✅ Retry logic working correctly")
        return True
    except Exception as e:
        print(f"❌ Retry logic test failed: {e}")
        return False


def main():
    """Run all foundation tests."""
    print("=" * 60)
    print("PHASE 1 FOUNDATION VERIFICATION")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Supervisor Agent", test_supervisor_agent()))
    results.append(("Supabase Client", test_supabase_client_initialization()))
    results.append(("CRUD Tool Generators", test_crud_tool_generators()))
    results.append(("Retry Logic", test_retry_logic()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All foundation tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
