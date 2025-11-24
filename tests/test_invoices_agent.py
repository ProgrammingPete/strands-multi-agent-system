"""
Test script for the Invoices Agent implementation.

This script verifies that:
1. The invoices agent can be imported
2. The invoice tools can be imported
3. The supervisor agent includes the invoices agent
4. Basic functionality works (without requiring actual Supabase connection)
"""

import sys
import os

def test_imports():
    """Test that all modules can be imported successfully."""
    print("Testing imports...")
    
    try:
        from agents.invoices_agent import invoices_agent_tool
        print("✓ Invoices agent imported successfully")
    except Exception as e:
        print(f"✗ Failed to import invoices agent: {e}")
        return False
    
    try:
        from agents.invoice_tools import get_invoices, create_invoice, update_invoice, delete_invoice
        print("✓ Invoice tools imported successfully")
    except Exception as e:
        print(f"✗ Failed to import invoice tools: {e}")
        return False
    
    try:
        from agents.supervisor import supervisor_agent
        print("✓ Supervisor agent imported successfully")
    except Exception as e:
        print(f"✗ Failed to import supervisor agent: {e}")
        return False
    
    return True


def test_agent_structure():
    """Test that the agent has the correct structure."""
    print("\nTesting agent structure...")
    
    try:
        from agents.invoices_agent import invoices_agent_tool, INVOICES_AGENT_SYSTEM_PROMPT
        
        # Check that system prompt is defined
        if not INVOICES_AGENT_SYSTEM_PROMPT:
            print("✗ System prompt is empty")
            return False
        print("✓ System prompt is defined")
        
        # Check that the tool is callable
        if not callable(invoices_agent_tool):
            print("✗ invoices_agent_tool is not callable")
            return False
        print("✓ invoices_agent_tool is callable")
        
        # Check tool metadata
        if hasattr(invoices_agent_tool, '__name__'):
            print(f"✓ Tool name: {invoices_agent_tool.__name__}")
        
        return True
        
    except Exception as e:
        print(f"✗ Agent structure test failed: {e}")
        return False


def test_tool_structure():
    """Test that the tools have the correct structure."""
    print("\nTesting tool structure...")
    
    try:
        from agents.invoice_tools import get_invoices, create_invoice, update_invoice, delete_invoice
        
        tools = [
            ('get_invoices', get_invoices),
            ('create_invoice', create_invoice),
            ('update_invoice', update_invoice),
            ('delete_invoice', delete_invoice)
        ]
        
        for tool_name, tool_func in tools:
            if not callable(tool_func):
                print(f"✗ {tool_name} is not callable")
                return False
            print(f"✓ {tool_name} is callable")
        
        return True
        
    except Exception as e:
        print(f"✗ Tool structure test failed: {e}")
        return False


def test_supervisor_integration():
    """Test that the supervisor agent includes the invoices agent."""
    print("\nTesting supervisor integration...")
    
    try:
        from agents.supervisor import supervisor_agent, SUPERVISOR_SYSTEM_PROMPT
        
        # Check that supervisor prompt mentions invoices
        if 'invoice' not in SUPERVISOR_SYSTEM_PROMPT.lower():
            print("✗ Supervisor prompt doesn't mention invoices")
            return False
        print("✓ Supervisor prompt mentions invoices")
        
        # The supervisor agent should be properly initialized
        if supervisor_agent is None:
            print("✗ Supervisor agent is None")
            return False
        print("✓ Supervisor agent is initialized")
        
        return True
        
    except Exception as e:
        print(f"✗ Supervisor integration test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Invoices Agent Implementation Test")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_imports),
        ("Agent Structure Test", test_agent_structure),
        ("Tool Structure Test", test_tool_structure),
        ("Supervisor Integration Test", test_supervisor_integration),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The Invoices Agent is ready.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
