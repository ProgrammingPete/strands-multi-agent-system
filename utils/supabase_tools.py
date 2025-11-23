"""
Generic CRUD tool generators for Supabase operations.

This module provides factory functions to generate Strands tools for common
database operations (Create, Read, Update, Delete) on Supabase tables.
"""

import json
import logging
from typing import Optional, Dict, Any, List, Callable
from strands import tool
from .supabase_client import get_supabase_client, SupabaseQueryError

logger = logging.getLogger(__name__)


def create_get_records_tool(
    table_name: str,
    tool_name: Optional[str] = None,
    description: Optional[str] = None,
    default_limit: int = 10,
    max_limit: int = 100
) -> Callable:
    """
    Create a tool for fetching records from a Supabase table.
    
    Args:
        table_name: Name of the Supabase table
        tool_name: Optional custom name for the tool (defaults to get_{table_name})
        description: Optional custom description
        default_limit: Default number of records to return
        max_limit: Maximum number of records allowed
    
    Returns:
        A Strands tool function for fetching records
    
    Example:
        >>> get_invoices = create_get_records_tool("invoices")
        >>> result = get_invoices(user_id="123", status="paid", limit=5)
    """
    tool_name = tool_name or f"get_{table_name}"
    description = description or f"Fetch records from the {table_name} table"
    
    @tool(name=tool_name)
    def get_records(
        user_id: str,
        filters: Optional[str] = None,
        limit: int = default_limit,
        order_by: Optional[str] = None,
        order_desc: bool = True
    ) -> str:
        f"""
        {description}
        
        Args:
            user_id: The user ID to fetch records for
            filters: Optional JSON string of filters (e.g., {{"status": "active", "priority": "high"}})
            limit: Maximum number of records to return (max {max_limit})
            order_by: Optional field to order by (defaults to 'created_at')
            order_desc: Whether to order descending (default True)
        
        Returns:
            JSON string of records or error message
        """
        try:
            supabase = get_supabase_client()
            
            # Validate limit
            limit = min(limit, max_limit)
            
            # Build query
            query = supabase.table(table_name).select('*').eq('user_id', user_id)
            
            # Apply filters if provided
            if filters:
                try:
                    filter_dict = json.loads(filters)
                    for key, value in filter_dict.items():
                        query = query.eq(key, value)
                except json.JSONDecodeError as e:
                    return json.dumps({
                        "error": f"Invalid filters JSON: {str(e)}",
                        "user_message": "The filter format is invalid. Please provide valid JSON."
                    })
            
            # Apply ordering
            order_field = order_by or 'created_at'
            query = query.order(order_field, desc=order_desc)
            
            # Apply limit
            query = query.limit(limit)
            
            # Execute query with retry logic
            result = supabase.execute_query(lambda: query.execute())
            
            logger.info(f"Successfully fetched {len(result.data)} records from {table_name}")
            
            return json.dumps({
                "success": True,
                "data": result.data,
                "count": len(result.data)
            })
            
        except SupabaseQueryError as e:
            logger.error(f"Failed to fetch records from {table_name}: {str(e)}")
            return json.dumps({
                "error": str(e),
                "user_message": f"Failed to retrieve {table_name}. Please try again."
            })
        except Exception as e:
            logger.error(f"Unexpected error fetching records from {table_name}: {str(e)}")
            return json.dumps({
                "error": str(e),
                "user_message": "An unexpected error occurred. Please try again."
            })
    
    return get_records


def create_create_record_tool(
    table_name: str,
    required_fields: List[str],
    tool_name: Optional[str] = None,
    description: Optional[str] = None
) -> Callable:
    """
    Create a tool for creating records in a Supabase table.
    
    Args:
        table_name: Name of the Supabase table
        required_fields: List of required field names
        tool_name: Optional custom name for the tool (defaults to create_{table_name})
        description: Optional custom description
    
    Returns:
        A Strands tool function for creating records
    
    Example:
        >>> create_invoice = create_create_record_tool(
        ...     "invoices",
        ...     required_fields=["user_id", "client_id", "amount"]
        ... )
        >>> result = create_invoice(data='{"user_id": "123", "client_id": "456", "amount": 1000}')
    """
    tool_name = tool_name or f"create_{table_name.rstrip('s')}"
    description = description or f"Create a new record in the {table_name} table"
    
    @tool(name=tool_name)
    def create_record(data: str) -> str:
        f"""
        {description}
        
        Args:
            data: JSON string containing the record data. Required fields: {', '.join(required_fields)}
        
        Returns:
            JSON string with created record or error message
        """
        try:
            supabase = get_supabase_client()
            
            # Parse input data
            try:
                record_data = json.loads(data)
            except json.JSONDecodeError as e:
                return json.dumps({
                    "error": f"Invalid JSON: {str(e)}",
                    "user_message": "The data format is invalid. Please provide valid JSON."
                })
            
            # Validate required fields
            missing_fields = [field for field in required_fields if field not in record_data]
            if missing_fields:
                return json.dumps({
                    "error": f"Missing required fields: {', '.join(missing_fields)}",
                    "user_message": f"Please provide the following required fields: {', '.join(missing_fields)}"
                })
            
            # Execute insert with retry logic
            result = supabase.execute_query(
                lambda: supabase.table(table_name).insert(record_data).execute()
            )
            
            logger.info(f"Successfully created record in {table_name}")
            
            return json.dumps({
                "success": True,
                "data": result.data[0] if result.data else None,
                "message": f"Successfully created {table_name.rstrip('s')}"
            })
            
        except SupabaseQueryError as e:
            logger.error(f"Failed to create record in {table_name}: {str(e)}")
            return json.dumps({
                "error": str(e),
                "user_message": f"Failed to create {table_name.rstrip('s')}. Please check your data and try again."
            })
        except Exception as e:
            logger.error(f"Unexpected error creating record in {table_name}: {str(e)}")
            return json.dumps({
                "error": str(e),
                "user_message": "An unexpected error occurred. Please try again."
            })
    
    return create_record


def create_update_record_tool(
    table_name: str,
    id_field: str = "id",
    tool_name: Optional[str] = None,
    description: Optional[str] = None
) -> Callable:
    """
    Create a tool for updating records in a Supabase table.
    
    Args:
        table_name: Name of the Supabase table
        id_field: Name of the ID field (defaults to 'id')
        tool_name: Optional custom name for the tool (defaults to update_{table_name})
        description: Optional custom description
    
    Returns:
        A Strands tool function for updating records
    
    Example:
        >>> update_invoice = create_update_record_tool("invoices")
        >>> result = update_invoice(
        ...     record_id="abc-123",
        ...     data='{"status": "paid", "paid_at": "2024-01-01"}'
        ... )
    """
    tool_name = tool_name or f"update_{table_name.rstrip('s')}"
    description = description or f"Update an existing record in the {table_name} table"
    
    @tool(name=tool_name)
    def update_record(record_id: str, data: str, user_id: Optional[str] = None) -> str:
        f"""
        {description}
        
        Args:
            record_id: The ID of the record to update
            data: JSON string containing the fields to update
            user_id: Optional user ID for authorization check
        
        Returns:
            JSON string with updated record or error message
        """
        try:
            supabase = get_supabase_client()
            
            # Parse update data
            try:
                update_data = json.loads(data)
            except json.JSONDecodeError as e:
                return json.dumps({
                    "error": f"Invalid JSON: {str(e)}",
                    "user_message": "The data format is invalid. Please provide valid JSON."
                })
            
            # Build query
            query = supabase.table(table_name).update(update_data).eq(id_field, record_id)
            
            # Add user_id filter if provided (for authorization)
            if user_id:
                query = query.eq('user_id', user_id)
            
            # Execute update with retry logic
            result = supabase.execute_query(lambda: query.execute())
            
            if not result.data:
                return json.dumps({
                    "error": "Record not found or unauthorized",
                    "user_message": f"Could not find or update the {table_name.rstrip('s')}. Please check the ID."
                })
            
            logger.info(f"Successfully updated record in {table_name}")
            
            return json.dumps({
                "success": True,
                "data": result.data[0] if result.data else None,
                "message": f"Successfully updated {table_name.rstrip('s')}"
            })
            
        except SupabaseQueryError as e:
            logger.error(f"Failed to update record in {table_name}: {str(e)}")
            return json.dumps({
                "error": str(e),
                "user_message": f"Failed to update {table_name.rstrip('s')}. Please try again."
            })
        except Exception as e:
            logger.error(f"Unexpected error updating record in {table_name}: {str(e)}")
            return json.dumps({
                "error": str(e),
                "user_message": "An unexpected error occurred. Please try again."
            })
    
    return update_record


def create_delete_record_tool(
    table_name: str,
    id_field: str = "id",
    tool_name: Optional[str] = None,
    description: Optional[str] = None,
    soft_delete: bool = False,
    soft_delete_field: str = "deleted_at"
) -> Callable:
    """
    Create a tool for deleting records from a Supabase table.
    
    Args:
        table_name: Name of the Supabase table
        id_field: Name of the ID field (defaults to 'id')
        tool_name: Optional custom name for the tool (defaults to delete_{table_name})
        description: Optional custom description
        soft_delete: Whether to use soft delete (set a timestamp) instead of hard delete
        soft_delete_field: Field name for soft delete timestamp
    
    Returns:
        A Strands tool function for deleting records
    
    Example:
        >>> delete_invoice = create_delete_record_tool("invoices")
        >>> result = delete_invoice(record_id="abc-123", user_id="123")
    """
    tool_name = tool_name or f"delete_{table_name.rstrip('s')}"
    description = description or f"Delete a record from the {table_name} table"
    
    @tool(name=tool_name)
    def delete_record(record_id: str, user_id: str, confirm: bool = False) -> str:
        f"""
        {description}
        
        Args:
            record_id: The ID of the record to delete
            user_id: The user ID for authorization
            confirm: Must be True to confirm deletion
        
        Returns:
            JSON string with deletion result or error message
        """
        try:
            # Require explicit confirmation
            if not confirm:
                return json.dumps({
                    "error": "Deletion not confirmed",
                    "user_message": "Please confirm that you want to delete this record by setting confirm=True"
                })
            
            supabase = get_supabase_client()
            
            if soft_delete:
                # Soft delete: update the deleted_at field
                from datetime import datetime
                update_data = {soft_delete_field: datetime.utcnow().isoformat()}
                
                query = supabase.table(table_name).update(update_data).eq(id_field, record_id).eq('user_id', user_id)
                result = supabase.execute_query(lambda: query.execute())
            else:
                # Hard delete: remove the record
                query = supabase.table(table_name).delete().eq(id_field, record_id).eq('user_id', user_id)
                result = supabase.execute_query(lambda: query.execute())
            
            if not result.data:
                return json.dumps({
                    "error": "Record not found or unauthorized",
                    "user_message": f"Could not find or delete the {table_name.rstrip('s')}. Please check the ID."
                })
            
            logger.info(f"Successfully deleted record from {table_name}")
            
            return json.dumps({
                "success": True,
                "message": f"Successfully deleted {table_name.rstrip('s')}"
            })
            
        except SupabaseQueryError as e:
            logger.error(f"Failed to delete record from {table_name}: {str(e)}")
            return json.dumps({
                "error": str(e),
                "user_message": f"Failed to delete {table_name.rstrip('s')}. Please try again."
            })
        except Exception as e:
            logger.error(f"Unexpected error deleting record from {table_name}: {str(e)}")
            return json.dumps({
                "error": str(e),
                "user_message": "An unexpected error occurred. Please try again."
            })
    
    return delete_record


# Convenience function to create a full CRUD toolset
def create_crud_toolset(
    table_name: str,
    required_fields: List[str],
    id_field: str = "id",
    default_limit: int = 10,
    max_limit: int = 100,
    soft_delete: bool = False
) -> Dict[str, Callable]:
    """
    Create a complete CRUD toolset for a Supabase table.
    
    Args:
        table_name: Name of the Supabase table
        required_fields: List of required fields for creation
        id_field: Name of the ID field
        default_limit: Default limit for get operations
        max_limit: Maximum limit for get operations
        soft_delete: Whether to use soft delete
    
    Returns:
        Dictionary with 'get', 'create', 'update', 'delete' tool functions
    
    Example:
        >>> invoice_tools = create_crud_toolset(
        ...     "invoices",
        ...     required_fields=["user_id", "client_id", "amount"]
        ... )
        >>> # Use the tools
        >>> result = invoice_tools['get'](user_id="123")
        >>> result = invoice_tools['create'](data='{"user_id": "123", ...}')
    """
    return {
        'get': create_get_records_tool(
            table_name=table_name,
            default_limit=default_limit,
            max_limit=max_limit
        ),
        'create': create_create_record_tool(
            table_name=table_name,
            required_fields=required_fields
        ),
        'update': create_update_record_tool(
            table_name=table_name,
            id_field=id_field
        ),
        'delete': create_delete_record_tool(
            table_name=table_name,
            id_field=id_field,
            soft_delete=soft_delete
        )
    }
