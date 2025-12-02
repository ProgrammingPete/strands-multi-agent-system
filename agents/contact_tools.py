"""
Supabase tools for contact operations.

This module provides specialized tools for contact management including
get, create, update, and delete operations on the contacts table.
"""

import json
import logging
from typing import Optional
from strands import tool
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.tool_utils import get_supabase_client_for_operation, AuthenticationError
from utils.supabase_client import SupabaseQueryError

logger = logging.getLogger(__name__)


@tool
def get_contacts(
    user_id: str,
    user_jwt: Optional[str] = None,
    contact_type: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 10
) -> str:
    """
    Fetch contacts from Supabase for a specific user.
    
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
        
        client, is_user_scoped = get_supabase_client_for_operation(user_id, user_jwt)
        limit = min(limit, 100)
        
        if is_user_scoped:
            query = client.schema("api").table('contacts').select('*')
        else:
            query = client.table('contacts').select('*')
        
        if contact_type:
            query = query.eq('contact_type', contact_type)
        if search:
            query = query.or_(f"name.ilike.%{search}%,email.ilike.%{search}%")
        
        query = query.order('name', desc=False).limit(limit)
        result = query.execute() if is_user_scoped else client.execute_query(lambda: query.execute())
        
        logger.info(f"Successfully fetched {len(result.data)} contacts for user {user_id}")
        return json.dumps({"success": True, "data": result.data, "count": len(result.data)})
        
    except AuthenticationError as e:
        return json.dumps({"error": e.message, "code": e.code, "user_message": e.user_message})
    except (SupabaseQueryError, Exception) as e:
        logger.error(f"Error fetching contacts: {str(e)}")
        return json.dumps({"error": str(e), "user_message": "Failed to retrieve contacts."})


@tool
def create_contact(user_id: str, data: str, user_jwt: Optional[str] = None) -> str:
    """Create a new contact in Supabase for a specific user."""
    try:
        if not user_id:
            return json.dumps({"error": "user_id is required", "user_message": "User identification is required."})
        
        client, is_user_scoped = get_supabase_client_for_operation(user_id, user_jwt)
        
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
        
        if is_user_scoped:
            result = client.schema("api").table('contacts').insert(contact_data).execute()
        else:
            result = client.execute_query(lambda: client.table('contacts').insert(contact_data).execute())
        
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
def delete_contact(user_id: str, contact_id: str, confirm: bool = False, user_jwt: Optional[str] = None) -> str:
    """Delete a contact from Supabase."""
    try:
        if not user_id:
            return json.dumps({"error": "user_id is required", "user_message": "User identification is required."})
        if not confirm:
            return json.dumps({"error": "Deletion not confirmed", "user_message": "Please confirm deletion."})
        
        client, is_user_scoped = get_supabase_client_for_operation(user_id, user_jwt)
        
        if is_user_scoped:
            result = client.schema("api").table('contacts').delete().eq('id', contact_id).execute()
        else:
            result = client.execute_query(lambda: client.table('contacts').delete().eq('id', contact_id).execute())
        
        if not result.data:
            return json.dumps({"error": "Contact not found", "user_message": "Could not find the contact to delete."})
        
        logger.info(f"Successfully deleted contact {contact_id} for user {user_id}")
        return json.dumps({"success": True, "message": "Successfully deleted contact"})
        
    except AuthenticationError as e:
        return json.dumps({"error": e.message, "code": e.code, "user_message": e.user_message})
    except (SupabaseQueryError, Exception) as e:
        logger.error(f"Error deleting contact: {str(e)}")
        return json.dumps({"error": str(e), "user_message": "Failed to delete contact."})
