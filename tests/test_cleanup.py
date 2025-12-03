"""
Test data cleanup utilities.

This module provides utilities for tracking and cleaning up test data
created during test execution.

**Requirements: 12.5** - Track created test data and remove it after test completion
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from contextlib import contextmanager

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.supabase_client import get_supabase_client, SupabaseQueryError

logger = logging.getLogger(__name__)


# Tables that support test data cleanup
CLEANABLE_TABLES = [
    'invoices',
    'projects',
    'appointments',
    'proposals',
    'contacts',
    'reviews',
    'campaigns',
    'tasks',
    'goals'
]


class TestDataCleanupManager:
    """
    Manager for tracking and cleaning up test data.
    
    This class provides a centralized way to track test data created
    during test execution and clean it up afterwards.
    
    **Requirements: 12.5**
    
    Usage:
        manager = TestDataCleanupManager()
        
        # Track created records
        manager.track('invoices', invoice_id)
        manager.track('projects', project_id)
        
        # Clean up all tracked records
        manager.cleanup_all()
    """
    
    def __init__(self, user_id: Optional[str] = None):
        """
        Initialize the cleanup manager.
        
        Args:
            user_id: Optional user ID for filtering cleanup operations.
                    If not provided, uses SYSTEM_USER_ID from environment.
        """
        self.user_id = user_id or os.getenv(
            "SYSTEM_USER_ID", 
            "00000000-0000-0000-0000-000000000000"
        )
        self._tracked_records: Dict[str, Set[str]] = {
            table: set() for table in CLEANABLE_TABLES
        }
        self._cleanup_errors: List[Dict[str, Any]] = []
        self._supabase = None
    
    @property
    def supabase(self):
        """Lazy-load Supabase client."""
        if self._supabase is None:
            self._supabase = get_supabase_client()
        return self._supabase
    
    def track(self, table_name: str, record_id: str) -> None:
        """
        Track a record for later cleanup.
        
        Args:
            table_name: Name of the table (e.g., 'invoices')
            record_id: UUID of the record to track
        """
        if table_name not in self._tracked_records:
            logger.warning(f"Unknown table '{table_name}' - adding to tracking")
            self._tracked_records[table_name] = set()
        
        self._tracked_records[table_name].add(record_id)
        logger.debug(f"Tracking {table_name} record: {record_id}")
    
    def untrack(self, table_name: str, record_id: str) -> None:
        """
        Remove a record from tracking (e.g., if already deleted).
        
        Args:
            table_name: Name of the table
            record_id: UUID of the record to untrack
        """
        if table_name in self._tracked_records:
            self._tracked_records[table_name].discard(record_id)
    
    def get_tracked_count(self, table_name: Optional[str] = None) -> int:
        """
        Get the count of tracked records.
        
        Args:
            table_name: Optional table name to filter by
            
        Returns:
            Number of tracked records
        """
        if table_name:
            return len(self._tracked_records.get(table_name, set()))
        return sum(len(records) for records in self._tracked_records.values())
    
    def cleanup_table(self, table_name: str) -> Dict[str, Any]:
        """
        Clean up all tracked records for a specific table.
        
        Args:
            table_name: Name of the table to clean up
            
        Returns:
            Dict with cleanup results (deleted_count, failed_count, errors)
        """
        if table_name not in self._tracked_records:
            return {"deleted_count": 0, "failed_count": 0, "errors": []}
        
        record_ids = list(self._tracked_records[table_name])
        deleted_count = 0
        failed_count = 0
        errors = []
        
        for record_id in record_ids:
            try:
                result = self.supabase.table(table_name).delete().eq('id', record_id).execute()
                if result.data:
                    deleted_count += 1
                    self._tracked_records[table_name].discard(record_id)
                    logger.debug(f"Deleted {table_name} record: {record_id}")
                else:
                    # Record may not exist (already deleted or never created)
                    self._tracked_records[table_name].discard(record_id)
                    logger.debug(f"Record {record_id} not found in {table_name}")
            except Exception as e:
                failed_count += 1
                error_info = {
                    "table": table_name,
                    "record_id": record_id,
                    "error": str(e)
                }
                errors.append(error_info)
                self._cleanup_errors.append(error_info)
                logger.warning(f"Failed to delete {table_name} record {record_id}: {e}")
        
        return {
            "deleted_count": deleted_count,
            "failed_count": failed_count,
            "errors": errors
        }
    
    def cleanup_all(self) -> Dict[str, Any]:
        """
        Clean up all tracked records across all tables.
        
        Returns:
            Dict with cleanup summary for all tables
        """
        logger.info("Starting test data cleanup...")
        
        results = {}
        total_deleted = 0
        total_failed = 0
        
        for table_name in CLEANABLE_TABLES:
            if self._tracked_records.get(table_name):
                result = self.cleanup_table(table_name)
                results[table_name] = result
                total_deleted += result["deleted_count"]
                total_failed += result["failed_count"]
        
        summary = {
            "total_deleted": total_deleted,
            "total_failed": total_failed,
            "tables": results,
            "errors": self._cleanup_errors
        }
        
        logger.info(
            f"Cleanup complete: {total_deleted} deleted, {total_failed} failed"
        )
        
        return summary
    
    def clear_tracking(self) -> None:
        """Clear all tracked records without deleting them."""
        for table_name in self._tracked_records:
            self._tracked_records[table_name] = set()
        self._cleanup_errors = []
    
    def get_cleanup_errors(self) -> List[Dict[str, Any]]:
        """Get list of cleanup errors that occurred."""
        return self._cleanup_errors.copy()


@contextmanager
def test_data_context(user_id: Optional[str] = None):
    """
    Context manager for automatic test data cleanup.
    
    Usage:
        with test_data_context() as tracker:
            # Create test data
            invoice_id = create_test_invoice()
            tracker.track('invoices', invoice_id)
            
            # Run tests...
            
        # Cleanup happens automatically when exiting context
    
    **Requirements: 12.5**
    
    Args:
        user_id: Optional user ID for the test context
        
    Yields:
        TestDataCleanupManager instance
    """
    manager = TestDataCleanupManager(user_id=user_id)
    
    try:
        yield manager
    finally:
        # Always cleanup, even if tests fail
        summary = manager.cleanup_all()
        
        if summary["total_failed"] > 0:
            logger.warning(
                f"Test data cleanup had {summary['total_failed']} failures. "
                f"Errors: {summary['errors']}"
            )


def cleanup_test_invoices_by_prefix(prefix: str = "INV-TEST-") -> Dict[str, Any]:
    """
    Clean up test invoices by invoice number prefix.
    
    This is useful for cleaning up test data that wasn't properly tracked.
    
    Args:
        prefix: Invoice number prefix to match (default: "INV-TEST-")
        
    Returns:
        Dict with cleanup results
    """
    supabase = get_supabase_client()
    user_id = os.getenv("SYSTEM_USER_ID", "00000000-0000-0000-0000-000000000000")
    
    try:
        # Find test invoices
        result = supabase.table('invoices').select('id, invoice_number').like(
            'invoice_number', f'{prefix}%'
        ).execute()
        
        if not result.data:
            return {"deleted_count": 0, "message": "No test invoices found"}
        
        deleted_count = 0
        failed_count = 0
        
        for invoice in result.data:
            try:
                supabase.table('invoices').delete().eq('id', invoice['id']).execute()
                deleted_count += 1
                logger.info(f"Deleted test invoice: {invoice['invoice_number']}")
            except Exception as e:
                failed_count += 1
                logger.warning(f"Failed to delete invoice {invoice['id']}: {e}")
        
        return {
            "deleted_count": deleted_count,
            "failed_count": failed_count,
            "message": f"Cleaned up {deleted_count} test invoices"
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up test invoices: {e}")
        return {"error": str(e)}


def cleanup_all_test_data_for_user(user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Clean up all test data for a specific user.
    
    WARNING: This will delete ALL data for the specified user.
    Use with caution - intended for test cleanup only.
    
    Args:
        user_id: User ID to clean up data for. Defaults to SYSTEM_USER_ID.
        
    Returns:
        Dict with cleanup results for each table
    """
    user_id = user_id or os.getenv(
        "SYSTEM_USER_ID", 
        "00000000-0000-0000-0000-000000000000"
    )
    
    supabase = get_supabase_client()
    results = {}
    
    for table_name in CLEANABLE_TABLES:
        try:
            # Delete all records for this user
            result = supabase.table(table_name).delete().eq('user_id', user_id).execute()
            deleted_count = len(result.data) if result.data else 0
            results[table_name] = {
                "deleted_count": deleted_count,
                "success": True
            }
            logger.info(f"Deleted {deleted_count} records from {table_name} for user {user_id}")
        except Exception as e:
            results[table_name] = {
                "deleted_count": 0,
                "success": False,
                "error": str(e)
            }
            logger.warning(f"Failed to clean up {table_name} for user {user_id}: {e}")
    
    return results


if __name__ == "__main__":
    """Run cleanup utilities from command line."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test data cleanup utilities")
    parser.add_argument(
        "--prefix", 
        default="INV-TEST-",
        help="Invoice number prefix to clean up"
    )
    parser.add_argument(
        "--user-id",
        help="User ID to clean up data for (defaults to SYSTEM_USER_ID)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Clean up ALL data for the user (use with caution)"
    )
    
    args = parser.parse_args()
    
    if args.all:
        print(f"Cleaning up ALL test data for user: {args.user_id or 'SYSTEM_USER_ID'}")
        results = cleanup_all_test_data_for_user(args.user_id)
        print(json.dumps(results, indent=2))
    else:
        print(f"Cleaning up test invoices with prefix: {args.prefix}")
        results = cleanup_test_invoices_by_prefix(args.prefix)
        print(json.dumps(results, indent=2))
