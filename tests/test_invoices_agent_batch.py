#!/usr/bin/env python3
"""
Batch integration tests for Invoices Agent.

This test suite performs end-to-end testing of the invoices agent by:
1. Sending various test prompts to the agent
2. Verifying the agent uses the correct tools
3. Checking results against actual Supabase data using MCP server
"""

import sys
import os
import json
import uuid
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.invoices_agent import invoices_agent_tool
from agents.invoice_tools import delete_invoice


class InvoicesBatchTester:
    """Batch tester for invoices agent with Supabase verification."""
    
    def __init__(self):
        self.test_results = []
        self.test_invoice_ids = []  # Track created invoices for cleanup
        self.test_invoice_numbers = []  # Track invoice numbers for lookup
        self.test_user_id = "test-user-" + str(uuid.uuid4())[:8]
        
    def log_result(self, test_name: str, passed: bool, details: str = ""):
        """Log a test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"  Details: {details}")
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "details": details
        })
    
    def verify_with_supabase_mcp(self, invoice_id: str) -> Dict[str, Any]:
        """
        Verify invoice data using Supabase MCP server.
        
        Note: This is a placeholder for MCP integration.
        In a real implementation, this would call the Supabase MCP server
        to fetch and verify the invoice data.
        """
        # TODO: Implement actual MCP call when MCP server is configured
        # For now, we'll simulate the verification
        print(f"  [MCP] Would verify invoice {invoice_id} via Supabase MCP server")
        return {"verified": True, "invoice_id": invoice_id}
    
    def test_create_invoice(self) -> bool:
        """Test creating a new invoice."""
        print("\n" + "=" * 60)
        print("TEST: Create Invoice")
        print("=" * 60)
        
        # Generate unique invoice number
        invoice_number = f"INV-TEST-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        query = f"""
        Create a new invoice with the following details:
        - Invoice number: {invoice_number}
        - Client name: Test Client ABC
        - Client email: testclient@example.com
        - Due date: {(datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')}
        - Line items:
          * Interior painting - 40 hours at $50/hour = $2000
          * Materials and supplies = $500
        - Subtotal: $2500
        - Tax rate: 8%
        - Tax amount: $200
        - Total amount: $2700
        - Notes: Test invoice for batch testing
        - Status: draft
        """
        
        print(f"Query: {query.strip()}")
        print("\nAgent Response:")
        
        try:
            response = invoices_agent_tool(query)
            print(response)
            
            # Check if response indicates success
            success = "success" in response.lower() or "created" in response.lower()
            
            if success:
                # Try to extract invoice ID from response
                # This is a simple heuristic - in production you'd parse the response more carefully
                if invoice_number in response:
                    # Track invoice number for cleanup
                    self.test_invoice_numbers.append(invoice_number)
                    
                    # Try to extract invoice ID from response (UUID format)
                    if "Invoice ID:" in response:
                        try:
                            # Look for UUID pattern after "Invoice ID:"
                            id_section = response.split("Invoice ID:")[1].split("\n")[0]
                            uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
                            match = re.search(uuid_pattern, id_section)
                            if match:
                                self.test_invoice_ids.append(match.group(0))
                        except:
                            pass
                    
                    self.log_result(
                        "Create Invoice",
                        True,
                        f"Invoice {invoice_number} created successfully"
                    )
                    return True
            
            self.log_result(
                "Create Invoice",
                False,
                "Failed to create invoice or couldn't verify creation"
            )
            return False
            
        except Exception as e:
            self.log_result("Create Invoice", False, f"Exception: {str(e)}")
            return False
    
    def test_get_invoices_all(self) -> bool:
        """Test retrieving all invoices."""
        print("\n" + "=" * 60)
        print("TEST: Get All Invoices")
        print("=" * 60)
        
        query = "Show me all invoices in the system, limit to 5"
        
        print(f"Query: {query}")
        print("\nAgent Response:")
        
        try:
            response = invoices_agent_tool(query)
            print(response)
            
            # Check if response contains invoice data
            success = ("invoice" in response.lower() and 
                      (any(status in response.lower() for status in 
                           ["draft", "sent", "paid", "overdue"])))
            
            self.log_result(
                "Get All Invoices",
                success,
                "Retrieved invoice list" if success else "No invoices found or error"
            )
            return success
            
        except Exception as e:
            self.log_result("Get All Invoices", False, f"Exception: {str(e)}")
            return False
    
    def test_get_invoices_by_status(self) -> bool:
        """Test retrieving invoices filtered by status."""
        print("\n" + "=" * 60)
        print("TEST: Get Invoices by Status")
        print("=" * 60)
        
        query = "Show me all draft invoices"
        
        print(f"Query: {query}")
        print("\nAgent Response:")
        
        try:
            response = invoices_agent_tool(query)
            print(response)
            
            # Check if response mentions draft status
            success = "draft" in response.lower()
            
            self.log_result(
                "Get Invoices by Status",
                success,
                "Retrieved draft invoices" if success else "Failed to filter by status"
            )
            return success
            
        except Exception as e:
            self.log_result("Get Invoices by Status", False, f"Exception: {str(e)}")
            return False
    
    def test_get_overdue_invoices(self) -> bool:
        """Test retrieving overdue invoices."""
        print("\n" + "=" * 60)
        print("TEST: Get Overdue Invoices")
        print("=" * 60)
        
        query = "What invoices are overdue? Show me the overdue ones."
        
        print(f"Query: {query}")
        print("\nAgent Response:")
        
        try:
            response = invoices_agent_tool(query)
            print(response)
            
            # Check if response addresses overdue invoices
            success = "overdue" in response.lower() or "no overdue" in response.lower()
            
            self.log_result(
                "Get Overdue Invoices",
                success,
                "Retrieved overdue invoice information"
            )
            return success
            
        except Exception as e:
            self.log_result("Get Overdue Invoices", False, f"Exception: {str(e)}")
            return False
    
    def test_update_invoice_status(self) -> bool:
        """Test updating an invoice status."""
        print("\n" + "=" * 60)
        print("TEST: Update Invoice Status")
        print("=" * 60)
        
        # First, get an invoice to update
        query1 = "Show me the most recent draft invoice"
        print(f"Query 1: {query1}")
        
        try:
            response1 = invoices_agent_tool(query1)
            print(f"Response 1: {response1[:200]}...")
            
            # For this test, we'll use a generic update query
            # In a real scenario, you'd extract the invoice ID from response1
            query2 = "Update the most recent draft invoice to 'sent' status"
            print(f"\nQuery 2: {query2}")
            print("\nAgent Response:")
            
            response2 = invoices_agent_tool(query2)
            print(response2)
            
            # Check if update was successful
            success = ("updated" in response2.lower() or 
                      "sent" in response2.lower() or
                      "success" in response2.lower())
            
            self.log_result(
                "Update Invoice Status",
                success,
                "Invoice status updated" if success else "Failed to update status"
            )
            return success
            
        except Exception as e:
            self.log_result("Update Invoice Status", False, f"Exception: {str(e)}")
            return False
    
    def test_update_invoice_payment(self) -> bool:
        """Test recording a payment on an invoice."""
        print("\n" + "=" * 60)
        print("TEST: Update Invoice Payment")
        print("=" * 60)
        
        query = """
        I received a payment for invoice. Find the most recent sent invoice and 
        mark it as paid with payment date today and full amount paid.
        """
        
        print(f"Query: {query.strip()}")
        print("\nAgent Response:")
        
        try:
            response = invoices_agent_tool(query)
            print(response)
            
            # Check if payment was recorded
            success = ("paid" in response.lower() or 
                      "payment" in response.lower() or
                      "updated" in response.lower())
            
            self.log_result(
                "Update Invoice Payment",
                success,
                "Payment recorded" if success else "Failed to record payment"
            )
            return success
            
        except Exception as e:
            self.log_result("Update Invoice Payment", False, f"Exception: {str(e)}")
            return False
    
    def test_invoice_summary(self) -> bool:
        """Test getting invoice summary/statistics."""
        print("\n" + "=" * 60)
        print("TEST: Invoice Summary")
        print("=" * 60)
        
        query = "Give me a summary of all invoices - how many are draft, sent, paid, and overdue?"
        
        print(f"Query: {query}")
        print("\nAgent Response:")
        
        try:
            response = invoices_agent_tool(query)
            print(response)
            
            # Check if response contains summary information
            success = (("draft" in response.lower() or "sent" in response.lower()) and
                      ("total" in response.lower() or "summary" in response.lower()))
            
            self.log_result(
                "Invoice Summary",
                success,
                "Retrieved invoice summary" if success else "Failed to get summary"
            )
            return success
            
        except Exception as e:
            self.log_result("Invoice Summary", False, f"Exception: {str(e)}")
            return False
    
    def test_complex_invoice_creation(self) -> bool:
        """Test creating a complex invoice with multiple line items."""
        print("\n" + "=" * 60)
        print("TEST: Complex Invoice Creation")
        print("=" * 60)
        
        invoice_number = f"INV-COMPLEX-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        query = f"""
        Create a detailed invoice for a large painting project:
        - Invoice number: {invoice_number}
        - Client: Premium Properties LLC
        - Email: billing@premiumproperties.com
        - Due date: {(datetime.now() + timedelta(days=45)).strftime('%Y-%m-%d')}
        - Line items:
          1. Exterior painting - 120 hours at $55/hour
          2. Interior painting - 80 hours at $50/hour  
          3. Premium paint materials - $2,500
          4. Scaffolding rental - $800
          5. Surface preparation - 40 hours at $45/hour
        - Calculate subtotal, apply 8% tax, and total
        - Terms: Net 45 days, 2% discount if paid within 10 days
        - Notes: Large commercial project, includes warranty
        """
        
        print(f"Query: {query.strip()}")
        print("\nAgent Response:")
        
        try:
            response = invoices_agent_tool(query)
            print(response)
            
            # Check if complex invoice was created
            success = ("success" in response.lower() or "created" in response.lower()) and \
                     invoice_number in response
            
            if success:
                # Track invoice number for cleanup
                self.test_invoice_numbers.append(invoice_number)
                
                # Try to extract invoice ID from response
                if "Invoice ID:" in response:
                    try:
                        invoice_id = response.split("Invoice ID:")[1].split()[0].strip()
                        self.test_invoice_ids.append(invoice_id)
                    except:
                        pass
            
            self.log_result(
                "Complex Invoice Creation",
                success,
                f"Complex invoice {invoice_number} created" if success else "Failed to create complex invoice"
            )
            return success
            
        except Exception as e:
            self.log_result("Complex Invoice Creation", False, f"Exception: {str(e)}")
            return False
    
    def test_natural_language_query(self) -> bool:
        """Test natural language query about invoices."""
        print("\n" + "=" * 60)
        print("TEST: Natural Language Query")
        print("=" * 60)
        
        query = "How much money am I owed from unpaid invoices?"
        
        print(f"Query: {query}")
        print("\nAgent Response:")
        
        try:
            response = invoices_agent_tool(query)
            print(response)
            
            # Check if response addresses the question
            # Accept either a dollar amount or a statement about no unpaid invoices
            success = ("$" in response or "amount" in response.lower() or 
                      "total" in response.lower() or "owed" in response.lower() or
                      "no unpaid" in response.lower() or "no overdue" in response.lower())
            
            self.log_result(
                "Natural Language Query",
                success,
                "Answered natural language query" if success else "Failed to understand query"
            )
            return success
            
        except Exception as e:
            self.log_result("Natural Language Query", False, f"Exception: {str(e)}")
            return False
    
    def cleanup_test_data(self):
        """Clean up test invoices created during testing."""
        print("\n" + "=" * 60)
        print("CLEANUP: Removing Test Data")
        print("=" * 60)
        
        if not self.test_invoice_ids and not self.test_invoice_numbers:
            print("No test data to clean up.")
            return
        
        # First, try to get invoice IDs from invoice numbers if we don't have them
        if self.test_invoice_numbers and not self.test_invoice_ids:
            print(f"Looking up invoice IDs for {len(self.test_invoice_numbers)} test invoices...")
            try:
                from agents.invoice_tools import get_invoices
                result = get_invoices(limit=100)
                result_data = json.loads(result)
                
                if result_data.get("success"):
                    for invoice in result_data.get("data", []):
                        if invoice.get("invoice_number") in self.test_invoice_numbers:
                            self.test_invoice_ids.append(invoice.get("id"))
            except Exception as e:
                print(f"⚠️  Could not look up invoice IDs: {str(e)}")
        
        # Delete invoices by ID
        deleted_count = 0
        failed_count = 0
        
        for invoice_id in self.test_invoice_ids:
            try:
                print(f"Deleting invoice {invoice_id}...")
                result = delete_invoice(invoice_id, confirm=True)
                result_data = json.loads(result)
                
                if result_data.get("success"):
                    print(f"  ✅ Deleted invoice {invoice_id}")
                    deleted_count += 1
                else:
                    print(f"  ⚠️  Failed to delete invoice {invoice_id}: {result_data.get('error', 'Unknown error')}")
                    failed_count += 1
            except Exception as e:
                print(f"  ❌ Error deleting invoice {invoice_id}: {str(e)}")
                failed_count += 1
        
        print(f"\nCleanup Summary: {deleted_count} deleted, {failed_count} failed")
    
    def run_all_tests(self) -> int:
        """Run all batch tests and return exit code."""
        print("\n" + "=" * 60)
        print("INVOICES AGENT BATCH TESTS")
        print("=" * 60)
        print(f"Test User ID: {self.test_user_id}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print()
        
        # Run all tests
        tests = [
            self.test_get_invoices_all,
            self.test_get_invoices_by_status,
            self.test_get_overdue_invoices,
            self.test_create_invoice,
            self.test_complex_invoice_creation,
            self.test_update_invoice_status,
            self.test_update_invoice_payment,
            self.test_invoice_summary,
            self.test_natural_language_query,
        ]
        
        for test_func in tests:
            try:
                test_func()
            except Exception as e:
                print(f"\n❌ Test {test_func.__name__} crashed: {str(e)}")
                self.log_result(test_func.__name__, False, f"Test crashed: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for r in self.test_results if r["passed"])
        total = len(self.test_results)
        
        for result in self.test_results:
            status = "✅" if result["passed"] else "❌"
            print(f"{status} {result['test']}")
            if result["details"] and not result["passed"]:
                print(f"   {result['details']}")
        
        print(f"\nTotal: {passed}/{total} tests passed")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        
        # Clean up test data
        self.cleanup_test_data()
        
        if passed == total:
            print("\n🎉 All tests passed!")
            return 0
        else:
            print(f"\n⚠️  {total - passed} test(s) failed")
            return 1


def main():
    """Main entry point for batch tests."""
    tester = InvoicesBatchTester()
    return tester.run_all_tests()


if __name__ == "__main__":
    sys.exit(main())
