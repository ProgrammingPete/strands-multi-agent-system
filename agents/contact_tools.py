"""
Supabase tools for contact operations with optimization features.

This module provides specialized tools for contact management including
get, create, update, and delete operations on the contacts table.

Optimizations implemented:
- Caching for frequently accessed contact lists
- Batch operations for bulk contact management
- Connection pooling for improved performance
"""

import json
import logging
from typing import Optional, List, Dict, Any
from strands import tool
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.tool_utils import get_supabase_client_for_operation, AuthenticationError
from utils.supabase_client import SupabaseQueryError
from utils.supabase_cache import cached_query, get_cache
from utils.supabase_batch import batch_insert_records, batch_update_records, batch_delete_records
from utils.supabase_pool import with_pooled_connection

logger = logging.getLogger(__name__)


@tool
@cached_query("contacts", ttl=300)  # Cache for 5 minutes
async def get_contacts(
    user_id: str,
    user_jwt: Optional[str] = None,
    contact_type: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 10
) -> str:
    """
    Fetch contacts from Supabase for a specific user with caching.
    
    Optimizations:
    - Results cached for 5 minutes to reduce API calls
    - Connection pooling for improved performance
    - Efficient query with proper indexing
    
    Args:
        user_id: User ID to fetch contacts for (required)
        user_jwt: Optional JWT token for user-scoped client creation
        contact_type: Optional type filter (client, supplier, lead, other)
        search: Optional search term for name or email
        limit: Maximum number of contacts to return (default 10, max 100)
    """
    try:
        if not user_id:
            return json.dumps({"error": "user_id is required", "user_message": "User identification is required."})
        
        # Use connection pooling for better performance
        async def fetch_contacts(client):
            limit_capped = min(limit, 100)
            
            if user_jwt:
                query = client.schema("api").table('contacts').select('*')
            else:
                query = client.schema("api").table('contacts').select('*').eq('user_id', user_id)
            
            if contact_type:
                query = query.eq('contact_type', contact_type)
            if search:
                query = query.or_(f"name.ilike.%{search}%,email.ilike.%{search}%")
            
            query = query.order('name', desc=False).limit(limit_capped)
            return query.execute()
        
        result = await with_pooled_connection(fetch_contacts, user_id, user_jwt)
        
        logger.info(f"Successfully fetched {len(result.data)} contacts for user {user_id}")
        return json.dumps({"success": True, "data": result.data, "count": len(result.data)})
        
    except AuthenticationError as e:
        return json.dumps({"error": e.message, "code": e.code, "user_message": e.user_message})
    except (SupabaseQueryError, Exception) as e:
        logger.error(f"Error fetching contacts: {str(e)}")
        return json.dumps({"error": str(e), "user_message": "Failed to retrieve contacts."})


@tool
async def create_contact(user_id: str, data: str, user_jwt: Optional[str] = None) -> str:
    """
    Create a new contact in Supabase for a specific user.
    
    Optimizations:
    - Invalidates cache after creation
    - Uses connection pooling
    """
    try:
        if not user_id:
            return json.dumps({"error": "user_id is required", "user_message": "User identification is required."})
        
        try:
            contact_data = json.loads(data)
        except json.JSONDecodeError as e:
            return json.dumps({"error": f"Invalid JSON: {str(e)}", "user_message": "Invalid data format."})
        
        required_fields = ['name']
        missing = [f for f in required_fields if f not in contact_data]
        if missing:
            return json.dumps({"error": f"Missing: {', '.join(missing)}", "user_message": f"Please provide: {', '.join(missing)}"})
        
        contact_data.setdefault('contact_type', 'client')
        contact_data['user_id'] = user_id
        
        # Use connection pooling for better performance
        async def create_contact_op(client):
            if user_jwt:
                return client.schema("api").table('contacts').insert(contact_data).execute()
            else:
                return client.schema("api").table('contacts').insert(contact_data).execute()
        
        result = await with_pooled_connection(create_contact_op, user_id, user_jwt)
        
        # Invalidate cache after creation
        cache = get_cache()
        await cache.invalidate_table(user_id, "contacts")
        
        logger.info(f"Successfully created contact for user {user_id}")
        return json.dumps({"success": True, "data": result.data[0] if result.data else None, "message": "Successfully created contact"})
        
    except AuthenticationError as e:
        return json.dumps({"error": e.message, "code": e.code, "user_message": e.user_message})
    except (SupabaseQueryError, Exception) as e:
        logger.error(f"Error creating contact: {str(e)}")
        return json.dumps({"error": str(e), "user_message": "Failed to create contact."})


@tool
def update_contact(user_id: str, contact_id: str, data: str, user_jwt: Optional[str] = None) -> str:
    """Update an existing contact in Supabase."""
    try:
        if not user_id:
            return json.dumps({"error": "user_id is required", "user_message": "User identification is required."})
        
        client, is_user_scoped = get_supabase_client_for_operation(user_id, user_jwt)
        
        try:
            update_data = json.loads(data)
        except json.JSONDecodeError as e:
            return json.dumps({"error": f"Invalid JSON: {str(e)}", "user_message": "Invalid data format."})
        
        if is_user_scoped:
            result = client.schema("api").table('contacts').update(update_data).eq('id', contact_id).execute()
        else:
            result = client.execute_query(lambda: client.table('contacts').update(update_data).eq('id', contact_id).execute())
        
        if not result.data:
            return json.dumps({"error": "Contact not found", "user_message": "Could not find the contact to update."})
        
        logger.info(f"Successfully updated contact {contact_id} for user {user_id}")
        return json.dumps({"success": True, "data": result.data[0] if result.data else None, "message": "Successfully updated contact"})
        
    except AuthenticationError as e:
        return json.dumps({"error": e.message, "code": e.code, "user_message": e.user_message})
    except (SupabaseQueryError, Exception) as e:
        logger.error(f"Error updating contact: {str(e)}")
        return json.dumps({"error": str(e), "user_message": "Failed to update contact."})


@tool
async def delete_contact(user_id: str, contact_id: str, confirm: bool = False, user_jwt: Optional[str] = None) -> str:
    """
    Delete a contact from Supabase.
    
    Optimizations:
    - Invalidates cache after deletion
    - Uses connection pooling
    """
    try:
        if not user_id:
            return json.dumps({"error": "user_id is required", "user_message": "User identification is required."})
        if not confirm:
            return json.dumps({"error": "Deletion not confirmed", "user_message": "Please confirm deletion."})
        
        # Use connection pooling for better performance
        async def delete_contact_op(client):
            if user_jwt:
                return client.schema("api").table('contacts').delete().eq('id', contact_id).execute()
            else:
                return client.schema("api").table('contacts').delete().eq('id', contact_id).eq('user_id', user_id).execute()
        
        result = await with_pooled_connection(delete_contact_op, user_id, user_jwt)
        
        if not result.data:
            return json.dumps({"error": "Contact not found", "user_message": "Could not find the contact to delete."})
        
        # Invalidate cache after deletion
        cache = get_cache()
        await cache.invalidate_table(user_id, "contacts")
        
        logger.info(f"Successfully deleted contact {contact_id} for user {user_id}")
        return json.dumps({"success": True, "message": "Successfully deleted contact"})
        
    except AuthenticationError as e:
        return json.dumps({"error": e.message, "code": e.code, "user_message": e.user_message})
    except (SupabaseQueryError, Exception) as e:
        logger.error(f"Error deleting contact: {str(e)}")
        return json.dumps({"error": str(e), "user_message": "Failed to delete contact."})


@tool
async def batch_create_contacts(user_id: str, contacts_data: str, user_jwt: Optional[str] = None) -> str:
    """
    Create multiple contacts in a single batch operation.
    
    Optimizations:
    - Reduces API calls by batching multiple inserts
    - Invalidates cache after batch creation
    - Better performance for bulk operations
    
    Args:
        user_id: User ID creating the contacts (required)
        contacts_data: JSON string containing array of contact data
        user_jwt: Optional JWT token for user-scoped client creation
    
    Returns:
        JSON string with batch creation results
    """
    try:
        if not user_id:
            return json.dumps({"error": "user_id is required", "user_message": "User identification is required."})
        
        try:
            contacts_list = json.loads(contacts_data)
            if not isinstance(contacts_list, list):
                return json.dumps({"error": "Expected array of contacts", "user_message": "Please provide an array of contact data."})
        except json.JSONDecodeError as e:
            return json.dumps({"error": f"Invalid JSON: {str(e)}", "user_message": "Invalid data format."})
        
        # Validate each contact
        for i, contact_data in enumerate(contacts_list):
            if 'name' not in contact_data:
                return json.dumps({"error": f"Contact {i+1} missing name", "user_message": f"Contact {i+1} is missing required field: name"})
            
            # Set defaults
            contact_data.setdefault('contact_type', 'client')
            contact_data['user_id'] = user_id
        
        # Execute batch insert
        result = await batch_insert_records("contacts", contacts_list, user_id, user_jwt)
        
        if result.success:
            # Invalidate cache after batch creation
            cache = get_cache()
            await cache.invalidate_table(user_id, "contacts")
            
            logger.info(f"Successfully batch created {len(contacts_list)} contacts for user {user_id}")
            return json.dumps({
                "success": True,
                "data": result.results,
                "count": len(result.results),
                "message": f"Successfully created {len(result.results)} contacts",
                "execution_time_ms": result.execution_time_ms
            })
        else:
            return json.dumps({
                "error": "Batch creation failed",
                "errors": result.errors,
                "user_message": "Failed to create some or all contacts. Please check the data and try again."
            })
        
    except Exception as e:
        logger.error(f"Error in batch contact creation: {str(e)}")
        return json.dumps({"error": str(e), "user_message": "Failed to create contacts in batch."})


@tool
async def batch_delete_contacts(user_id: str, contact_ids: str, confirm: bool = False, user_jwt: Optional[str] = None) -> str:
    """
    Delete multiple contacts in a single batch operation.
    
    Optimizations:
    - Reduces API calls by batching multiple deletes
    - Invalidates cache after batch deletion
    - Better performance for bulk operations
    
    Args:
        user_id: User ID performing the deletion (required)
        contact_ids: JSON string containing array of contact IDs to delete
        confirm: Must be True to confirm deletion (safety check)
        user_jwt: Optional JWT token for user-scoped client creation
    
    Returns:
        JSON string with batch deletion results
    """
    try:
        if not user_id:
            return json.dumps({"error": "user_id is required", "user_message": "User identification is required."})
        
        if not confirm:
            return json.dumps({"error": "Deletion not confirmed", "user_message": "Please confirm that you want to delete these contacts."})
        
        try:
            ids_list = json.loads(contact_ids)
            if not isinstance(ids_list, list):
                return json.dumps({"error": "Expected array of contact IDs", "user_message": "Please provide an array of contact IDs."})
        except json.JSONDecodeError as e:
            return json.dumps({"error": f"Invalid JSON: {str(e)}", "user_message": "Invalid data format."})
        
        # Execute batch delete
        result = await batch_delete_records("contacts", ids_list, user_id, user_jwt)
        
        if result.success:
            # Invalidate cache after batch deletion
            cache = get_cache()
            await cache.invalidate_table(user_id, "contacts")
            
            logger.info(f"Successfully batch deleted {len(ids_list)} contacts for user {user_id}")
            return json.dumps({
                "success": True,
                "count": len(result.results),
                "message": f"Successfully deleted {len(result.results)} contacts",
                "execution_time_ms": result.execution_time_ms
            })
        else:
            return json.dumps({
                "error": "Batch deletion failed",
                "errors": result.errors,
                "user_message": "Failed to delete some or all contacts."
            })
        
    except Exception as e:
        logger.error(f"Error in batch contact deletion: {str(e)}")
        return json.dumps({"error": str(e), "user_message": "Failed to delete contacts in batch."})
