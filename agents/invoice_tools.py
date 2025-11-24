"""
Supabase tools for invoice operations.

This module provides specialized tools for invoice management including
get, create, update, and delete operations on the invoices table.
"""

import json
import logging
from typing import Optional
from strands import tool
import sys
import os

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.supabase_client import get_supabase_client, SupabaseQueryError

logger = logging.getLogger(__name__)


@tool
def get_invoices(
    user_id: str,
    status: Optional[str] = None,
    client_id: Optional[str] = None,
    limit: int = 10
) -> str:
    """
    Fetch invoices from Supabase.
    
    Args:
        user_id: The user ID to fetch invoices for
        status: Optional status filter (draft, sent, viewed, partial, paid, overdue, cancelled)
        client_id: Optional client ID filter
        limit: Maximum number of invoices to return (default 10, max 100)
    
    Returns:
        JSON string of invoices with details including line items, amounts, and dates
    """
    try:
        supabase = get_supabase_client()
        
        # Validate limit
        limit = min(limit, 100)
        
        # Build query - Note: invoices table doesn't have user_id, so we'll fetch all
        # In production, you'd filter by user_id through a join or RLS policy
        query = supabase.table('invoices').select('*')
        
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
        
        # Execute query with retry logic
        result = supabase.execute_query(lambda: query.execute())
        
        logger.info(f"Successfully fetched {len(result.data)} invoices")
        
        return json.dumps({
            "success": True,
            "data": result.data,
            "count": len(result.data)
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
def create_invoice(data: str) -> str:
    """
    Create a new invoice in Supabase.
    
    Args:
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
    
    Returns:
        JSON string with created invoice or error message
    """
    try:
        supabase = get_supabase_client()
        
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
        
        # Execute insert with retry logic
        result = supabase.execute_query(
            lambda: supabase.table('invoices').insert(invoice_data).execute()
        )
        
        logger.info(f"Successfully created invoice: {invoice_data.get('invoice_number')}")
        
        return json.dumps({
            "success": True,
            "data": result.data[0] if result.data else None,
            "message": "Successfully created invoice"
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
def update_invoice(invoice_id: str, data: str) -> str:
    """
    Update an existing invoice in Supabase.
    
    Args:
        invoice_id: The UUID of the invoice to update
        data: JSON string containing fields to update. Can include:
            - status: Invoice status (draft, sent, viewed, partial, paid, overdue, cancelled)
            - paid_date: Date payment was received
            - amount_paid: Amount that has been paid
            - line_items: Updated line items
            - subtotal, tax_amount, discount_amount, total_amount: Financial updates
            - notes, terms: Additional information
            - Any other invoice fields
    
    Returns:
        JSON string with updated invoice or error message
    """
    try:
        supabase = get_supabase_client()
        
        # Parse update data
        try:
            update_data = json.loads(data)
        except json.JSONDecodeError as e:
            return json.dumps({
                "error": f"Invalid JSON: {str(e)}",
                "user_message": "The update data format is invalid. Please provide valid JSON."
            })
        
        # Build and execute update query
        query = supabase.table('invoices').update(update_data).eq('id', invoice_id)
        result = supabase.execute_query(lambda: query.execute())
        
        if not result.data:
            return json.dumps({
                "error": "Invoice not found",
                "user_message": "Could not find the invoice to update. Please check the invoice ID."
            })
        
        logger.info(f"Successfully updated invoice: {invoice_id}")
        
        return json.dumps({
            "success": True,
            "data": result.data[0] if result.data else None,
            "message": "Successfully updated invoice"
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
def delete_invoice(invoice_id: str, confirm: bool = False) -> str:
    """
    Delete an invoice from Supabase.
    
    Args:
        invoice_id: The UUID of the invoice to delete
        confirm: Must be True to confirm deletion (safety check)
    
    Returns:
        JSON string with deletion result or error message
    """
    try:
        # Require explicit confirmation
        if not confirm:
            return json.dumps({
                "error": "Deletion not confirmed",
                "user_message": "Please confirm that you want to delete this invoice. This action cannot be undone."
            })
        
        supabase = get_supabase_client()
        
        # Execute delete with retry logic
        query = supabase.table('invoices').delete().eq('id', invoice_id)
        result = supabase.execute_query(lambda: query.execute())
        
        if not result.data:
            return json.dumps({
                "error": "Invoice not found",
                "user_message": "Could not find the invoice to delete. Please check the invoice ID."
            })
        
        logger.info(f"Successfully deleted invoice: {invoice_id}")
        
        return json.dumps({
            "success": True,
            "message": "Successfully deleted invoice"
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
