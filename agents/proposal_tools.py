"""
Supabase tools for proposal operations.

This module provides specialized tools for proposal management including
get, create, update, and delete operations on the proposals table.
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
def get_proposals(
    user_id: str,
    user_jwt: Optional[str] = None,
    status: Optional[str] = None,
    client_id: Optional[str] = None,
    limit: int = 10
) -> str:
    """
    Fetch proposals from Supabase for a specific user.
    
    Args:
        user_id: User ID to fetch proposals for (required)
        user_jwt: Optional JWT token for user-scoped client creation
        status: Optional status filter (draft, sent, viewed, accepted, rejected, expired)
        client_id: Optional client ID filter
        limit: Maximum number of proposals to return (default 10, max 100)
    """
    try:
        if not user_id:
            return json.dumps({"error": "user_id is required", "user_message": "User identification is required."})
        
        client, is_user_scoped = get_supabase_client_for_operation(user_id, user_jwt)
        limit = min(limit, 100)
        
        if is_user_scoped:
            query = client.schema("api").table('proposals').select('*')
        else:
            query = client.table('proposals').select('*')
        
        if status:
            query = query.eq('status', status)
        if client_id:
            query = query.eq('client_id', client_id)
        
        query = query.order('created_at', desc=True).limit(limit)
        result = query.execute() if is_user_scoped else client.execute_query(lambda: query.execute())
        
        logger.info(f"Successfully fetched {len(result.data)} proposals for user {user_id}")
        return json.dumps({"success": True, "data": result.data, "count": len(result.data)})
        
    except AuthenticationError as e:
        return json.dumps({"error": e.message, "code": e.code, "user_message": e.user_message})
    except (SupabaseQueryError, Exception) as e:
        logger.error(f"Error fetching proposals: {str(e)}")
        return json.dumps({"error": str(e), "user_message": "Failed to retrieve proposals."})


@tool
def create_proposal(user_id: str, data: str, user_jwt: Optional[str] = None) -> str:
    """Create a new proposal in Supabase for a specific user."""
    try:
        if not user_id:
            return json.dumps({"error": "user_id is required", "user_message": "User identification is required."})
        
        client, is_user_scoped = get_supabase_client_for_operation(user_id, user_jwt)
        
        try:
            proposal_data = json.loads(data)
        except json.JSONDecodeError as e:
            return json.dumps({"error": f"Invalid JSON: {str(e)}", "user_message": "Invalid data format."})
        
        required_fields = ['title', 'client_name']
        missing = [f for f in required_fields if f not in proposal_data]
        if missing:
            return json.dumps({"error": f"Missing: {', '.join(missing)}", "user_message": f"Please provide: {', '.join(missing)}"})
        
        proposal_data.setdefault('status', 'draft')
        proposal_data['user_id'] = user_id
        
        if is_user_scoped:
            result = client.schema("api").table('proposals').insert(proposal_data).execute()
        else:
            result = client.execute_query(lambda: client.table('proposals').insert(proposal_data).execute())
        
        logger.info(f"Successfully created proposal for user {user_id}")
        return json.dumps({"success": True, "data": result.data[0] if result.data else None, "message": "Successfully created proposal"})
        
    except AuthenticationError as e:
        return json.dumps({"error": e.message, "code": e.code, "user_message": e.user_message})
    except (SupabaseQueryError, Exception) as e:
        logger.error(f"Error creating proposal: {str(e)}")
        return json.dumps({"error": str(e), "user_message": "Failed to create proposal."})


@tool
def update_proposal(user_id: str, proposal_id: str, data: str, user_jwt: Optional[str] = None) -> str:
    """Update an existing proposal in Supabase."""
    try:
        if not user_id:
            return json.dumps({"error": "user_id is required", "user_message": "User identification is required."})
        
        client, is_user_scoped = get_supabase_client_for_operation(user_id, user_jwt)
        
        try:
            update_data = json.loads(data)
        except json.JSONDecodeError as e:
            return json.dumps({"error": f"Invalid JSON: {str(e)}", "user_message": "Invalid data format."})
        
        if is_user_scoped:
            result = client.schema("api").table('proposals').update(update_data).eq('id', proposal_id).execute()
        else:
            result = client.execute_query(lambda: client.table('proposals').update(update_data).eq('id', proposal_id).execute())
        
        if not result.data:
            return json.dumps({"error": "Proposal not found", "user_message": "Could not find the proposal to update."})
        
        logger.info(f"Successfully updated proposal {proposal_id} for user {user_id}")
        return json.dumps({"success": True, "data": result.data[0] if result.data else None, "message": "Successfully updated proposal"})
        
    except AuthenticationError as e:
        return json.dumps({"error": e.message, "code": e.code, "user_message": e.user_message})
    except (SupabaseQueryError, Exception) as e:
        logger.error(f"Error updating proposal: {str(e)}")
        return json.dumps({"error": str(e), "user_message": "Failed to update proposal."})


@tool
def delete_proposal(user_id: str, proposal_id: str, confirm: bool = False, user_jwt: Optional[str] = None) -> str:
    """Delete a proposal from Supabase."""
    try:
        if not user_id:
            return json.dumps({"error": "user_id is required", "user_message": "User identification is required."})
        if not confirm:
            return json.dumps({"error": "Deletion not confirmed", "user_message": "Please confirm deletion."})
        
        client, is_user_scoped = get_supabase_client_for_operation(user_id, user_jwt)
        
        if is_user_scoped:
            result = client.schema("api").table('proposals').delete().eq('id', proposal_id).execute()
        else:
            result = client.execute_query(lambda: client.table('proposals').delete().eq('id', proposal_id).execute())
        
        if not result.data:
            return json.dumps({"error": "Proposal not found", "user_message": "Could not find the proposal to delete."})
        
        logger.info(f"Successfully deleted proposal {proposal_id} for user {user_id}")
        return json.dumps({"success": True, "message": "Successfully deleted proposal"})
        
    except AuthenticationError as e:
        return json.dumps({"error": e.message, "code": e.code, "user_message": e.user_message})
    except (SupabaseQueryError, Exception) as e:
        logger.error(f"Error deleting proposal: {str(e)}")
        return json.dumps({"error": str(e), "user_message": "Failed to delete proposal."})
