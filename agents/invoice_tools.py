"""
Supabase tools for invoice operations.

This module provides specialized tools for invoice management including
get, create, update, and delete operations on the invoices table.

All tools require a user_id parameter and optionally accept a user_jwt
for user-scoped operations with RLS enforcement.
"""

import json
import logging
from typing import Optional
from strands import tool
import sys
import os

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.supabase_client import get_supabase_client, SupabaseQueryError, SupabaseConnectionError

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """
    Raised when authentication fails for agent tool operations.
    
    Attributes:
        message: Technical error message for logging
        code: Error code for programmatic handling
        user_message: User-friendly error message for display
    """
    
    def __init__(self, message: str, code: str):
        self.message = message
        self.code = code
        self.user_message = self._get_user_message(code)
        super().__init__(self.message)
        
    def _get_user_message(self, code: str) -> str:
        """Get user-friendly error message based on error code."""
        messages = {
            "MISSING_TOKEN": "Authentication required. Please log in.",
            "MISSING_USER_ID": "User identification required.",
        }
        return messages.get(code, "Authentication error. Please try again.")


def _get_supabase_client_for_operation(user_id: str, user_jwt: Optional[str] = None):
    """
    Get the appropriate Supabase client based on environment and JWT availability.
    
    In production mode, JWT is required and a user-scoped client is created.
    In development mode, service key fallback is allowed with a warning.
    
    Args:
        user_id: The user ID for the operation (required)
        user_jwt: Optional JWT token for user-scoped client creation
        
    Returns:
        Tuple of (client, is_user_scoped) where:
            - client: Supabase client (either user-scoped or service key)
            - is_user_scoped: True if using user-scoped client with RLS
            
    Raises:
        AuthenticationError: If JWT is required but not provided (production mode)
    """
    environment = os.getenv("ENVIRONMENT", "development")
    supabase_wrapper = get_supabase_client()
    
    if user_jwt:
        # Production path: Use user-scoped client with RLS enforcement
        try:
            client = supabase_wrapper.create_user_scoped_client(user_jwt)
            logger.debug(f"Using user-scoped client for user {user_id}")
            return client, True
        except SupabaseConnectionError as e:
            logger.error(f"Failed to create user-scoped client: {str(e)}")
            if environment == "production":
                raise AuthenticationError(
                    f"Failed to create user-scoped client: {str(e)}",
                    "MISSING_TOKEN"
                )
            # Fall through to development fallback
            logger.warning("Falling back to service key client in development mode")
    
    if environment == "production":
        # Production without JWT: Fail securely
        raise AuthenticationError(
            "JWT required in production environment",
            "MISSING_TOKEN"
        )
    
    # Development path: Use service key (bypasses RLS)
    logger.warning(f"Using service key - RLS bypassed (development mode) for user {user_id}")
    return supabase_wrapper, False


@tool
def get_invoices(
    user_id: str,
    user_jwt: Optional[str] = None,
    status: Optional[str] = None,
    client_id: Optional[str] = None,
    limit: int = 10
) -> str:
    """
    Fetch invoices from Supabase for a specific user.
    RLS policies automatically filter by user_id when using user-scoped client.
    
    Args:
        user_id: User ID to fetch invoices for (required)
        user_jwt: Optional JWT token for user-scoped client creation
        status: Optional status filter (draft, sent, viewed, partial, paid, overdue, cancelled)
        client_id: Optional client ID filter
        limit: Maximum number of invoices to return (default 10, max 100)
    
    Returns:
        JSON string of invoices with details including line items, amounts, and dates
    """
    try:
        if not user_id:
            return json.dumps({
                "error": "user_id is required",
                "user_message": "User identification is required to fetch invoices."
            })
        
        client, is_user_scoped = _get_supabase_client_for_operation(user_id, user_jwt)
        
        # Validate limit
        limit = min(limit, 100)
        
        # Build query - RLS automatically filters by user_id when using user-scoped client
        if is_user_scoped:
            # User-scoped client: RLS handles filtering
            query = client.schema("api").table('invoices').select('*')
        else:
            # Service key client (development): Use wrapper's table method
            query = client.table('invoices').select('*')
        
        # Apply status filter if provided
        if status:
            query = query.eq('status', status)
        
        # Apply client filter if provided
        if client_id:
            query = query.eq('client_id', client_id)
        
        # Order by created date descending
        query = query.order('created_at', desc=True)
        
        # Apply limit
        query = query.limit(limit)
        
        # Execute query
        if is_user_scoped:
            result = query.execute()
        else:
            result = client.execute_query(lambda: query.execute())
        
        logger.info(f"Successfully fetched {len(result.data)} invoices for user {user_id}")
        
        return json.dumps({
            "success": True,
            "data": result.data,
            "count": len(result.data)
        })
        
    except AuthenticationError as e:
        logger.error(f"Authentication error fetching invoices: {str(e)}")
        return json.dumps({
            "error": e.message,
            "code": e.code,
            "user_message": e.user_message
        })
    except SupabaseQueryError as e:
        logger.error(f"Failed to fetch invoices: {str(e)}")
        return json.dumps({
            "error": str(e),
            "user_message": "Failed to retrieve invoices. Please try again."
        })
    except Exception as e:
        logger.error(f"Unexpected error fetching invoices: {str(e)}")
        return json.dumps({
            "error": str(e),
            "user_message": "An unexpected error occurred while fetching invoices. Please try again."
        })


@tool
def create_invoice(
    user_id: str,
    data: str,
    user_jwt: Optional[str] = None
) -> str:
    """
    Create a new invoice in Supabase for a specific user.
    The user_id is automatically set on the record for RLS enforcement.
    
    Args:
        user_id: User ID creating the invoice (required)
        data: JSON string containing invoice data. Required fields:
            - invoice_number: Unique invoice number
            - client_name: Name of the client
            - due_date: Due date for payment (YYYY-MM-DD format)
            - total_amount: Total invoice amount
            Optional fields:
            - client_id: UUID of the client
            - client_email: Client email address
            - project_id: UUID of associated project
            - issue_date: Invoice issue date (defaults to today)
            - subtotal: Subtotal before tax
            - tax_rate: Tax rate percentage
            - tax_amount: Tax amount
            - discount_amount: Discount amount
            - line_items: Array of line items with description, quantity, rate, amount
            - notes: Additional notes
            - terms: Payment terms
            - status: Invoice status (defaults to 'draft')
        user_jwt: Optional JWT token for user-scoped client creation
    
    Returns:
        JSON string with created invoice or error message
    """
    try:
        if not user_id:
            return json.dumps({
                "error": "user_id is required",
                "user_message": "User identification is required to create an invoice."
            })
        
        client, is_user_scoped = _get_supabase_client_for_operation(user_id, user_jwt)
        
        # Parse input data
        try:
            invoice_data = json.loads(data)
        except json.JSONDecodeError as e:
            return json.dumps({
                "error": f"Invalid JSON: {str(e)}",
                "user_message": "The invoice data format is invalid. Please provide valid JSON."
            })
        
        # Validate required fields
        required_fields = ['invoice_number', 'client_name', 'due_date', 'total_amount']
        missing_fields = [field for field in required_fields if field not in invoice_data]
        if missing_fields:
            return json.dumps({
                "error": f"Missing required fields: {', '.join(missing_fields)}",
                "user_message": f"Please provide the following required fields: {', '.join(missing_fields)}"
            })
        
        # Set default status if not provided
        if 'status' not in invoice_data:
            invoice_data['status'] = 'draft'
        
        # Set user_id on the record for RLS
        invoice_data['user_id'] = user_id
        
        # Execute insert
        if is_user_scoped:
            result = client.schema("api").table('invoices').insert(invoice_data).execute()
        else:
            result = client.execute_query(
                lambda: client.table('invoices').insert(invoice_data).execute()
            )
        
        logger.info(f"Successfully created invoice {invoice_data.get('invoice_number')} for user {user_id}")
        
        return json.dumps({
            "success": True,
            "data": result.data[0] if result.data else None,
            "message": "Successfully created invoice"
        })
        
    except AuthenticationError as e:
        logger.error(f"Authentication error creating invoice: {str(e)}")
        return json.dumps({
            "error": e.message,
            "code": e.code,
            "user_message": e.user_message
        })
    except SupabaseQueryError as e:
        logger.error(f"Failed to create invoice: {str(e)}")
        return json.dumps({
            "error": str(e),
            "user_message": "Failed to create invoice. Please check your data and try again."
        })
    except Exception as e:
        logger.error(f"Unexpected error creating invoice: {str(e)}")
        return json.dumps({
            "error": str(e),
            "user_message": "An unexpected error occurred while creating the invoice. Please try again."
        })


@tool
def update_invoice(
    user_id: str,
    invoice_id: str,
    data: str,
    user_jwt: Optional[str] = None
) -> str:
    """
    Update an existing invoice in Supabase.
    RLS policies ensure users can only update their own invoices.
    
    Args:
        user_id: User ID performing the update (required)
        invoice_id: The UUID of the invoice to update
        data: JSON string containing fields to update. Can include:
            - status: Invoice status (draft, sent, viewed, partial, paid, overdue, cancelled)
            - paid_date: Date payment was received
            - amount_paid: Amount that has been paid
            - line_items: Updated line items
            - subtotal, tax_amount, discount_amount, total_amount: Financial updates
            - notes, terms: Additional information
            - Any other invoice fields
        user_jwt: Optional JWT token for user-scoped client creation
    
    Returns:
        JSON string with updated invoice or error message
    """
    try:
        if not user_id:
            return json.dumps({
                "error": "user_id is required",
                "user_message": "User identification is required to update an invoice."
            })
        
        client, is_user_scoped = _get_supabase_client_for_operation(user_id, user_jwt)
        
        # Parse update data
        try:
            update_data = json.loads(data)
        except json.JSONDecodeError as e:
            return json.dumps({
                "error": f"Invalid JSON: {str(e)}",
                "user_message": "The update data format is invalid. Please provide valid JSON."
            })
        
        # Build and execute update query
        # RLS automatically ensures user can only update their own invoices
        if is_user_scoped:
            query = client.schema("api").table('invoices').update(update_data).eq('id', invoice_id)
            result = query.execute()
        else:
            query = client.table('invoices').update(update_data).eq('id', invoice_id)
            result = client.execute_query(lambda: query.execute())
        
        if not result.data:
            return json.dumps({
                "error": "Invoice not found or access denied",
                "user_message": "Could not find the invoice to update. Please check the invoice ID."
            })
        
        logger.info(f"Successfully updated invoice {invoice_id} for user {user_id}")
        
        return json.dumps({
            "success": True,
            "data": result.data[0] if result.data else None,
            "message": "Successfully updated invoice"
        })
        
    except AuthenticationError as e:
        logger.error(f"Authentication error updating invoice: {str(e)}")
        return json.dumps({
            "error": e.message,
            "code": e.code,
            "user_message": e.user_message
        })
    except SupabaseQueryError as e:
        logger.error(f"Failed to update invoice: {str(e)}")
        return json.dumps({
            "error": str(e),
            "user_message": "Failed to update invoice. Please try again."
        })
    except Exception as e:
        logger.error(f"Unexpected error updating invoice: {str(e)}")
        return json.dumps({
            "error": str(e),
            "user_message": "An unexpected error occurred while updating the invoice. Please try again."
        })


@tool
def delete_invoice(
    user_id: str,
    invoice_id: str,
    confirm: bool = False,
    user_jwt: Optional[str] = None
) -> str:
    """
    Delete an invoice from Supabase.
    RLS policies ensure users can only delete their own invoices.
    
    Args:
        user_id: User ID performing the deletion (required)
        invoice_id: The UUID of the invoice to delete
        confirm: Must be True to confirm deletion (safety check)
        user_jwt: Optional JWT token for user-scoped client creation
    
    Returns:
        JSON string with deletion result or error message
    """
    try:
        if not user_id:
            return json.dumps({
                "error": "user_id is required",
                "user_message": "User identification is required to delete an invoice."
            })
        
        # Require explicit confirmation
        if not confirm:
            return json.dumps({
                "error": "Deletion not confirmed",
                "user_message": "Please confirm that you want to delete this invoice. This action cannot be undone."
            })
        
        client, is_user_scoped = _get_supabase_client_for_operation(user_id, user_jwt)
        
        # Execute delete - RLS automatically ensures user can only delete their own invoices
        if is_user_scoped:
            query = client.schema("api").table('invoices').delete().eq('id', invoice_id)
            result = query.execute()
        else:
            query = client.table('invoices').delete().eq('id', invoice_id)
            result = client.execute_query(lambda: query.execute())
        
        if not result.data:
            return json.dumps({
                "error": "Invoice not found or access denied",
                "user_message": "Could not find the invoice to delete. Please check the invoice ID."
            })
        
        logger.info(f"Successfully deleted invoice {invoice_id} for user {user_id}")
        
        return json.dumps({
            "success": True,
            "message": "Successfully deleted invoice"
        })
        
    except AuthenticationError as e:
        logger.error(f"Authentication error deleting invoice: {str(e)}")
        return json.dumps({
            "error": e.message,
            "code": e.code,
            "user_message": e.user_message
        })
    except SupabaseQueryError as e:
        logger.error(f"Failed to delete invoice: {str(e)}")
        return json.dumps({
            "error": str(e),
            "user_message": "Failed to delete invoice. Please try again."
        })
    except Exception as e:
        logger.error(f"Unexpected error deleting invoice: {str(e)}")
        return json.dumps({
            "error": str(e),
            "user_message": "An unexpected error occurred while deleting the invoice. Please try again."
        })
