"""
Supabase tools for goal operations.

This module provides specialized tools for goal management including
get, create, update, and delete operations on the goals table.
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
def get_goals(
    user_id: str,
    user_jwt: Optional[str] = None,
    status: Optional[str] = None,
    goal_type: Optional[str] = None,
    limit: int = 10
) -> str:
    """
    Fetch goals from Supabase for a specific user.
    
    Args:
        user_id: User ID to fetch goals for (required)
        user_jwt: Optional JWT token for user-scoped client creation
        status: Optional status filter (not_started, in_progress, completed, abandoned)
        goal_type: Optional type filter (revenue, project, personal, team)
        limit: Maximum number of goals to return (default 10, max 100)
    """
    try:
        if not user_id:
            return json.dumps({"error": "user_id is required", "user_message": "User identification is required."})
        
        client, is_user_scoped = get_supabase_client_for_operation(user_id, user_jwt)
        limit = min(limit, 100)
        
        if is_user_scoped:
            query = client.schema("api").table('goals').select('*')
        else:
            query = client.table('goals').select('*')
        
        if status:
            query = query.eq('status', status)
        if goal_type:
            query = query.eq('goal_type', goal_type)
        
        query = query.order('target_date', desc=False).limit(limit)
        result = query.execute() if is_user_scoped else client.execute_query(lambda: query.execute())
        
        logger.info(f"Successfully fetched {len(result.data)} goals for user {user_id}")
        return json.dumps({"success": True, "data": result.data, "count": len(result.data)})
        
    except AuthenticationError as e:
        return json.dumps({"error": e.message, "code": e.code, "user_message": e.user_message})
    except (SupabaseQueryError, Exception) as e:
        logger.error(f"Error fetching goals: {str(e)}")
        return json.dumps({"error": str(e), "user_message": "Failed to retrieve goals."})


@tool
def create_goal(user_id: str, data: str, user_jwt: Optional[str] = None) -> str:
    """Create a new goal in Supabase for a specific user."""
    try:
        if not user_id:
            return json.dumps({"error": "user_id is required", "user_message": "User identification is required."})
        
        client, is_user_scoped = get_supabase_client_for_operation(user_id, user_jwt)
        
        try:
            goal_data = json.loads(data)
        except json.JSONDecodeError as e:
            return json.dumps({"error": f"Invalid JSON: {str(e)}", "user_message": "Invalid data format."})
        
        required_fields = ['title']
        missing = [f for f in required_fields if f not in goal_data]
        if missing:
            return json.dumps({"error": f"Missing: {', '.join(missing)}", "user_message": f"Please provide: {', '.join(missing)}"})
        
        goal_data.setdefault('status', 'not_started')
        goal_data.setdefault('progress', 0)
        goal_data['user_id'] = user_id
        
        if is_user_scoped:
            result = client.schema("api").table('goals').insert(goal_data).execute()
        else:
            result = client.execute_query(lambda: client.table('goals').insert(goal_data).execute())
        
        logger.info(f"Successfully created goal for user {user_id}")
        return json.dumps({"success": True, "data": result.data[0] if result.data else None, "message": "Successfully created goal"})
        
    except AuthenticationError as e:
        return json.dumps({"error": e.message, "code": e.code, "user_message": e.user_message})
    except (SupabaseQueryError, Exception) as e:
        logger.error(f"Error creating goal: {str(e)}")
        return json.dumps({"error": str(e), "user_message": "Failed to create goal."})


@tool
def update_goal(user_id: str, goal_id: str, data: str, user_jwt: Optional[str] = None) -> str:
    """Update an existing goal in Supabase."""
    try:
        if not user_id:
            return json.dumps({"error": "user_id is required", "user_message": "User identification is required."})
        
        client, is_user_scoped = get_supabase_client_for_operation(user_id, user_jwt)
        
        try:
            update_data = json.loads(data)
        except json.JSONDecodeError as e:
            return json.dumps({"error": f"Invalid JSON: {str(e)}", "user_message": "Invalid data format."})
        
        if is_user_scoped:
            result = client.schema("api").table('goals').update(update_data).eq('id', goal_id).execute()
        else:
            result = client.execute_query(lambda: client.table('goals').update(update_data).eq('id', goal_id).execute())
        
        if not result.data:
            return json.dumps({"error": "Goal not found", "user_message": "Could not find the goal to update."})
        
        logger.info(f"Successfully updated goal {goal_id} for user {user_id}")
        return json.dumps({"success": True, "data": result.data[0] if result.data else None, "message": "Successfully updated goal"})
        
    except AuthenticationError as e:
        return json.dumps({"error": e.message, "code": e.code, "user_message": e.user_message})
    except (SupabaseQueryError, Exception) as e:
        logger.error(f"Error updating goal: {str(e)}")
        return json.dumps({"error": str(e), "user_message": "Failed to update goal."})


@tool
def delete_goal(user_id: str, goal_id: str, confirm: bool = False, user_jwt: Optional[str] = None) -> str:
    """Delete a goal from Supabase."""
    try:
        if not user_id:
            return json.dumps({"error": "user_id is required", "user_message": "User identification is required."})
        if not confirm:
            return json.dumps({"error": "Deletion not confirmed", "user_message": "Please confirm deletion."})
        
        client, is_user_scoped = get_supabase_client_for_operation(user_id, user_jwt)
        
        if is_user_scoped:
            result = client.schema("api").table('goals').delete().eq('id', goal_id).execute()
        else:
            result = client.execute_query(lambda: client.table('goals').delete().eq('id', goal_id).execute())
        
        if not result.data:
            return json.dumps({"error": "Goal not found", "user_message": "Could not find the goal to delete."})
        
        logger.info(f"Successfully deleted goal {goal_id} for user {user_id}")
        return json.dumps({"success": True, "message": "Successfully deleted goal"})
        
    except AuthenticationError as e:
        return json.dumps({"error": e.message, "code": e.code, "user_message": e.user_message})
    except (SupabaseQueryError, Exception) as e:
        logger.error(f"Error deleting goal: {str(e)}")
        return json.dumps({"error": str(e), "user_message": "Failed to delete goal."})
