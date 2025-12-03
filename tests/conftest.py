"""
Pytest configuration and fixtures for test infrastructure.

This module provides centralized test fixtures that:
1. Use SYSTEM_USER_ID environment variable for test data operations
2. Associate test data with the system user account
3. Provide consistent user_id handling across all tests

**Requirements: 12.1, 12.2**
"""

import os
import uuid
import json
import logging
from typing import Optional, Generator, Dict, Any, List
from datetime import datetime, timedelta

import pytest
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =============================================================================
# SYSTEM USER FIXTURES
# =============================================================================

@pytest.fixture(scope="session")
def system_user_id() -> str:
    """
    Provide the system user ID for tests.
    
    This fixture returns the SYSTEM_USER_ID from environment variables,
    which should be used for all test data operations to ensure proper
    association with a known test user account.
    
    **Requirements: 12.1, 12.2**
    
    Returns:
        str: The system user ID (UUID format)
    """
    user_id = os.getenv("SYSTEM_USER_ID", "00000000-0000-0000-0000-000000000000")
    logger.info(f"Using SYSTEM_USER_ID for tests: {user_id}")
    return user_id


@pytest.fixture(scope="session")
def test_environment() -> str:
    """
    Provide the current test environment.
    
    Returns:
        str: The environment name (development, production, test)
    """
    return os.getenv("ENVIRONMENT", "development")


@pytest.fixture(scope="session")
def is_development_mode(test_environment: str) -> bool:
    """
    Check if running in development mode.
    
    Returns:
        bool: True if in development mode
    """
    return test_environment.lower() == "development"


# =============================================================================
# SUPABASE CLIENT FIXTURES
# =============================================================================

@pytest.fixture(scope="session")
def supabase_client():
    """
    Provide a Supabase client for test operations.
    
    This client uses the service key (in development) to bypass RLS
    for test setup and teardown operations.
    
    Returns:
        SupabaseClientWrapper: The Supabase client wrapper
    """
    from utils.supabase_client import get_supabase_client
    return get_supabase_client()


@pytest.fixture(scope="function")
def user_scoped_client(supabase_client, system_user_id):
    """
    Provide a user-scoped Supabase client for testing RLS.
    
    Note: This requires a valid JWT token. In development mode,
    this may fall back to the service key client.
    
    Returns:
        Client: A user-scoped Supabase client (or service key client in dev)
    """
    # In development, we use the service key client
    # In production tests, we would need a real JWT
    test_jwt = os.getenv("TEST_USER_JWT")
    
    if test_jwt:
        try:
            return supabase_client.create_user_scoped_client(test_jwt)
        except Exception as e:
            logger.warning(f"Could not create user-scoped client: {e}")
    
    # Fall back to service key client in development
    logger.warning("Using service key client - RLS will be bypassed")
    return supabase_client


# =============================================================================
# TEST DATA FIXTURES
# =============================================================================

@pytest.fixture(scope="function")
def test_invoice_data(system_user_id: str) -> Dict[str, Any]:
    """
    Provide test invoice data associated with the system user.
    
    **Requirements: 12.2**
    
    Returns:
        dict: Invoice data with user_id set to system user
    """
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    return {
        "user_id": system_user_id,
        "invoice_number": f"INV-TEST-{timestamp}-{uuid.uuid4().hex[:6]}",
        "client_name": "Test Client",
        "client_email": "test@example.com",
        "due_date": (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
        "issue_date": datetime.now().strftime('%Y-%m-%d'),
        "subtotal": 1000.00,
        "tax_rate": 8.0,
        "tax_amount": 80.00,
        "total_amount": 1080.00,
        "status": "draft",
        "notes": "Test invoice created by automated tests",
        "line_items": [
            {
                "description": "Test Service",
                "quantity": 10,
                "rate": 100.00,
                "amount": 1000.00
            }
        ]
    }


@pytest.fixture(scope="function")
def test_project_data(system_user_id: str) -> Dict[str, Any]:
    """
    Provide test project data associated with the system user.
    
    **Requirements: 12.2**
    
    Returns:
        dict: Project data with user_id set to system user
    """
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    return {
        "user_id": system_user_id,
        "name": f"Test Project {timestamp}",
        "description": "Test project created by automated tests",
        "status": "active",
        "start_date": datetime.now().strftime('%Y-%m-%d'),
        "end_date": (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d'),
        "budget": 10000.00
    }


@pytest.fixture(scope="function")
def test_contact_data(system_user_id: str) -> Dict[str, Any]:
    """
    Provide test contact data associated with the system user.
    
    **Requirements: 12.2**
    
    Returns:
        dict: Contact data with user_id set to system user
    """
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    return {
        "user_id": system_user_id,
        "name": f"Test Contact {timestamp}",
        "email": f"contact-{timestamp}@example.com",
        "phone": "555-0100",
        "type": "client",
        "notes": "Test contact created by automated tests"
    }


# =============================================================================
# TEST DATA TRACKING AND CLEANUP
# =============================================================================

class DataTracker:
    """
    Tracks test data created during tests for cleanup.
    
    **Requirements: 12.5**
    
    Note: Named 'DataTracker' instead of 'TestDataTracker' to avoid
    pytest trying to collect it as a test class.
    """
    
    def __init__(self):
        self.created_records: Dict[str, List[str]] = {
            'invoices': [],
            'projects': [],
            'appointments': [],
            'proposals': [],
            'contacts': [],
            'reviews': [],
            'campaigns': [],
            'tasks': [],
            'goals': []
        }
    
    def track(self, table_name: str, record_id: str) -> None:
        """Track a created record for later cleanup."""
        if table_name in self.created_records:
            self.created_records[table_name].append(record_id)
            logger.debug(f"Tracking {table_name} record: {record_id}")
    
    def get_tracked_records(self, table_name: str) -> List[str]:
        """Get all tracked records for a table."""
        return self.created_records.get(table_name, [])
    
    def clear(self, table_name: Optional[str] = None) -> None:
        """Clear tracked records for a table or all tables."""
        if table_name:
            self.created_records[table_name] = []
        else:
            for key in self.created_records:
                self.created_records[key] = []


@pytest.fixture(scope="function")
def test_data_tracker() -> DataTracker:
    """
    Provide a test data tracker for the current test.
    
    **Requirements: 12.5**
    
    Returns:
        DataTracker: A tracker instance for the test
    """
    return DataTracker()


@pytest.fixture(scope="function")
def cleanup_test_data(supabase_client, test_data_tracker) -> Generator[DataTracker, None, None]:
    """
    Fixture that provides test data tracking and automatic cleanup.
    
    Usage:
        def test_something(cleanup_test_data):
            # Create test data
            result = create_invoice(...)
            cleanup_test_data.track('invoices', result['id'])
            
            # Test assertions...
            
        # Cleanup happens automatically after test
    
    **Requirements: 12.5**
    
    Yields:
        DataTracker: The tracker to use for tracking created data
    """
    tracker = test_data_tracker
    
    yield tracker
    
    # Cleanup after test
    logger.info("Cleaning up test data...")
    cleanup_errors = []
    
    for table_name, record_ids in tracker.created_records.items():
        for record_id in record_ids:
            try:
                result = supabase_client.table(table_name).delete().eq('id', record_id).execute()
                logger.debug(f"Deleted {table_name} record: {record_id}")
            except Exception as e:
                cleanup_errors.append(f"{table_name}/{record_id}: {str(e)}")
                logger.warning(f"Failed to delete {table_name} record {record_id}: {e}")
    
    if cleanup_errors:
        logger.warning(f"Cleanup errors: {cleanup_errors}")
    
    tracker.clear()


# =============================================================================
# MOCK JWT FIXTURES (for testing without real auth)
# =============================================================================

@pytest.fixture(scope="function")
def mock_jwt_token(system_user_id: str) -> str:
    """
    Provide a mock JWT token for testing.
    
    Note: This is NOT a valid JWT - it's for testing code paths
    that handle JWT tokens. For actual RLS testing, use real JWTs.
    
    Returns:
        str: A mock JWT token string
    """
    # This is a placeholder - in real tests, you'd use Supabase Auth
    # to create a real test user and get their JWT
    return f"mock-jwt-for-user-{system_user_id}"


@pytest.fixture(scope="session")
def real_test_jwt() -> Optional[str]:
    """
    Provide a real JWT token for integration testing.
    
    This requires TEST_USER_JWT to be set in the environment.
    
    Returns:
        Optional[str]: The real JWT token or None if not configured
    """
    jwt = os.getenv("TEST_USER_JWT")
    if not jwt:
        logger.warning("TEST_USER_JWT not configured - some tests may be skipped")
    return jwt


# =============================================================================
# AGENT TOOL FIXTURES
# =============================================================================

@pytest.fixture(scope="function")
def invoice_tools_with_user(system_user_id: str):
    """
    Provide invoice tools configured with the system user ID.
    
    **Requirements: 12.3**
    
    Returns:
        dict: Dictionary of invoice tool functions with user_id pre-configured
    """
    from agents.invoice_tools import get_invoices, create_invoice, update_invoice, delete_invoice
    
    def get_invoices_for_user(**kwargs):
        return get_invoices(user_id=system_user_id, **kwargs)
    
    def create_invoice_for_user(data: str, **kwargs):
        return create_invoice(user_id=system_user_id, data=data, **kwargs)
    
    def update_invoice_for_user(invoice_id: str, data: str, **kwargs):
        return update_invoice(user_id=system_user_id, invoice_id=invoice_id, data=data, **kwargs)
    
    def delete_invoice_for_user(invoice_id: str, confirm: bool = False, **kwargs):
        return delete_invoice(user_id=system_user_id, invoice_id=invoice_id, confirm=confirm, **kwargs)
    
    return {
        'get_invoices': get_invoices_for_user,
        'create_invoice': create_invoice_for_user,
        'update_invoice': update_invoice_for_user,
        'delete_invoice': delete_invoice_for_user,
        'user_id': system_user_id
    }


# =============================================================================
# PYTEST CONFIGURATION
# =============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "requires_jwt: mark test as requiring a real JWT token"
    )
    config.addinivalue_line(
        "markers", "requires_supabase: mark test as requiring Supabase connection"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection based on environment."""
    # Skip tests that require JWT if not configured
    if not os.getenv("TEST_USER_JWT"):
        skip_jwt = pytest.mark.skip(reason="TEST_USER_JWT not configured")
        for item in items:
            if "requires_jwt" in item.keywords:
                item.add_marker(skip_jwt)
    
    # Skip tests that require Supabase if not configured
    if not os.getenv("SUPABASE_URL"):
        skip_supabase = pytest.mark.skip(reason="SUPABASE_URL not configured")
        for item in items:
            if "requires_supabase" in item.keywords:
                item.add_marker(skip_supabase)
