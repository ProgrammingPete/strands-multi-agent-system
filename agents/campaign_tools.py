"""
Supabase tools for campaign operations.

This module provides specialized tools for campaign management including
get, create, update, and delete operations on the campaigns table.
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
def get_campaigns(
    user_id: str,
    user_jwt: Optional[str] = None,
    status: Optional[str] = None,
    campaign_type: Optional[str] = None,
    limit: int = 10
) -> str:
    """
    Fetch campaigns from Supabase for a specific user.
    
    Args:
        user_id: User ID to fetch campaigns for (required)
        user_jwt: Optional JWT token for user-scoped client creation
        status: Optional status filter (draft, scheduled, active, paused, completed)
        campaign_type: Optional type filter (email, sms, social, direct_mail)
        limit: Maximum number of campaigns to return (default 10, max 100)
    """
    try:
        if not user_id:
            return json.dumps({"error": "user_id is required", "user_message": "User identification is required."})
        
        client, is_user_scoped = get_supabase_client_for_operation(user_id, user_jwt)
        limit = min(limit, 100)
        
        if is_user_scoped:
            query = client.schema("api").table('campaigns').select('*')
        else:
            query = client.table('campaigns').select('*')
        
        if status:
            query = query.eq('status', status)
        if campaign_type:
            query = query.eq('campaign_type', campaign_type)
        
        query = query.order('created_at', desc=True).limit(limit)
        result = query.execute() if is_user_scoped else client.execute_query(lambda: query.execute())
        
        logger.info(f"Successfully fetched {len(result.data)} campaigns for user {user_id}")
        return json.dumps({"success": True, "data": result.data, "count": len(result.data)})
        
    except AuthenticationError as e:
        return json.dumps({"error": e.message, "code": e.code, "user_message": e.user_message})
    except (SupabaseQueryError, Exception) as e:
        logger.error(f"Error fetching campaigns: {str(e)}")
        return json.dumps({"error": str(e), "user_message": "Failed to retrieve campaigns."})


@tool
def create_campaign(user_id: str, data: str, user_jwt: Optional[str] = None) -> str:
    """Create a new campaign in Supabase for a specific user."""
    try:
        if not user_id:
            return json.dumps({"error": "user_id is required", "user_message": "User identification is required."})
        
        client, is_user_scoped = get_supabase_client_for_operation(user_id, user_jwt)
        
        try:
            campaign_data = json.loads(data)
        except json.JSONDecodeError as e:
            return json.dumps({"error": f"Invalid JSON: {str(e)}", "user_message": "Invalid data format."})
        
        required_fields = ['name']
        missing = [f for f in required_fields if f not in campaign_data]
        if missing:
            return json.dumps({"error": f"Missing: {', '.join(missing)}", "user_message": f"Please provide: {', '.join(missing)}"})
        
        campaign_data.setdefault('status', 'draft')
        campaign_data['user_id'] = user_id
        
        if is_user_scoped:
            result = client.schema("api").table('campaigns').insert(campaign_data).execute()
        else:
            result = client.execute_query(lambda: client.table('campaigns').insert(campaign_data).execute())
        
        logger.info(f"Successfully created campaign for user {user_id}")
        return json.dumps({"success": True, "data": result.data[0] if result.data else None, "message": "Successfully created campaign"})
        
    except AuthenticationError as e:
        return json.dumps({"error": e.message, "code": e.code, "user_message": e.user_message})
    except (SupabaseQueryError, Exception) as e:
        logger.error(f"Error creating campaign: {str(e)}")
        return json.dumps({"error": str(e), "user_message": "Failed to create campaign."})


@tool
def update_campaign(user_id: str, campaign_id: str, data: str, user_jwt: Optional[str] = None) -> str:
    """Update an existing campaign in Supabase."""
    try:
        if not user_id:
            return json.dumps({"error": "user_id is required", "user_message": "User identification is required."})
        
        client, is_user_scoped = get_supabase_client_for_operation(user_id, user_jwt)
        
        try:
            update_data = json.loads(data)
        except json.JSONDecodeError as e:
            return json.dumps({"error": f"Invalid JSON: {str(e)}", "user_message": "Invalid data format."})
        
        if is_user_scoped:
            result = client.schema("api").table('campaigns').update(update_data).eq('id', campaign_id).execute()
        else:
            result = client.execute_query(lambda: client.table('campaigns').update(update_data).eq('id', campaign_id).execute())
        
        if not result.data:
            return json.dumps({"error": "Campaign not found", "user_message": "Could not find the campaign to update."})
        
        logger.info(f"Successfully updated campaign {campaign_id} for user {user_id}")
        return json.dumps({"success": True, "data": result.data[0] if result.data else None, "message": "Successfully updated campaign"})
        
    except AuthenticationError as e:
        return json.dumps({"error": e.message, "code": e.code, "user_message": e.user_message})
    except (SupabaseQueryError, Exception) as e:
        logger.error(f"Error updating campaign: {str(e)}")
        return json.dumps({"error": str(e), "user_message": "Failed to update campaign."})


@tool
def delete_campaign(user_id: str, campaign_id: str, confirm: bool = False, user_jwt: Optional[str] = None) -> str:
    """Delete a campaign from Supabase."""
    try:
        if not user_id:
            return json.dumps({"error": "user_id is required", "user_message": "User identification is required."})
        if not confirm:
            return json.dumps({"error": "Deletion not confirmed", "user_message": "Please confirm deletion."})
        
        client, is_user_scoped = get_supabase_client_for_operation(user_id, user_jwt)
        
        if is_user_scoped:
            result = client.schema("api").table('campaigns').delete().eq('id', campaign_id).execute()
        else:
            result = client.execute_query(lambda: client.table('campaigns').delete().eq('id', campaign_id).execute())
        
        if not result.data:
            return json.dumps({"error": "Campaign not found", "user_message": "Could not find the campaign to delete."})
        
        logger.info(f"Successfully deleted campaign {campaign_id} for user {user_id}")
        return json.dumps({"success": True, "message": "Successfully deleted campaign"})
        
    except AuthenticationError as e:
        return json.dumps({"error": e.message, "code": e.code, "user_message": e.user_message})
    except (SupabaseQueryError, Exception) as e:
        logger.error(f"Error deleting campaign: {str(e)}")
        return json.dumps({"error": str(e), "user_message": "Failed to delete campaign."})
