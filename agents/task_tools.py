"""
Supabase tools for task operations.

This module provides specialized tools for task management including
get, create, update, and delete operations on the tasks table.
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
def get_tasks(
    user_id: str,
    user_jwt: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    project_id: Optional[str] = None,
    limit: int = 10
) -> str:
    """
    Fetch tasks from Supabase for a specific user.
    
    Args:
        user_id: User ID to fetch tasks for (required)
        user_jwt: Optional JWT token for user-scoped client creation
        status: Optional status filter (todo, in_progress, completed, cancelled)
        priority: Optional priority filter (low, medium, high, urgent)
        project_id: Optional project ID filter
        limit: Maximum number of tasks to return (default 10, max 100)
    """
    try:
        if not user_id:
            return json.dumps({"error": "user_id is required", "user_message": "User identification is required."})
        
        client, is_user_scoped = get_supabase_client_for_operation(user_id, user_jwt)
        limit = min(limit, 100)
        
        if is_user_scoped:
            query = client.schema("api").table('tasks').select('*')
        else:
            query = client.table('tasks').select('*')
        
        if status:
            query = query.eq('status', status)
        if priority:
            query = query.eq('priority', priority)
        if project_id:
            query = query.eq('project_id', project_id)
        
        query = query.order('due_date', desc=False).limit(limit)
        result = query.execute() if is_user_scoped else client.execute_query(lambda: query.execute())
        
        logger.info(f"Successfully fetched {len(result.data)} tasks for user {user_id}")
        return json.dumps({"success": True, "data": result.data, "count": len(result.data)})
        
    except AuthenticationError as e:
        return json.dumps({"error": e.message, "code": e.code, "user_message": e.user_message})
    except (SupabaseQueryError, Exception) as e:
        logger.error(f"Error fetching tasks: {str(e)}")
        return json.dumps({"error": str(e), "user_message": "Failed to retrieve tasks."})


@tool
def create_task(user_id: str, data: str, user_jwt: Optional[str] = None) -> str:
    """Create a new task in Supabase for a specific user."""
    try:
        if not user_id:
            return json.dumps({"error": "user_id is required", "user_message": "User identification is required."})
        
        client, is_user_scoped = get_supabase_client_for_operation(user_id, user_jwt)
        
        try:
            task_data = json.loads(data)
        except json.JSONDecodeError as e:
            return json.dumps({"error": f"Invalid JSON: {str(e)}", "user_message": "Invalid data format."})
        
        required_fields = ['title']
        missing = [f for f in required_fields if f not in task_data]
        if missing:
            return json.dumps({"error": f"Missing: {', '.join(missing)}", "user_message": f"Please provide: {', '.join(missing)}"})
        
        task_data.setdefault('status', 'todo')
        task_data.setdefault('priority', 'medium')
        task_data['user_id'] = user_id
        
        if is_user_scoped:
            result = client.schema("api").table('tasks').insert(task_data).execute()
        else:
            result = client.execute_query(lambda: client.table('tasks').insert(task_data).execute())
        
        logger.info(f"Successfully created task for user {user_id}")
        return json.dumps({"success": True, "data": result.data[0] if result.data else None, "message": "Successfully created task"})
        
    except AuthenticationError as e:
        return json.dumps({"error": e.message, "code": e.code, "user_message": e.user_message})
    except (SupabaseQueryError, Exception) as e:
        logger.error(f"Error creating task: {str(e)}")
        return json.dumps({"error": str(e), "user_message": "Failed to create task."})


@tool
def update_task(user_id: str, task_id: str, data: str, user_jwt: Optional[str] = None) -> str:
    """Update an existing task in Supabase."""
    try:
        if not user_id:
            return json.dumps({"error": "user_id is required", "user_message": "User identification is required."})
        
        client, is_user_scoped = get_supabase_client_for_operation(user_id, user_jwt)
        
        try:
            update_data = json.loads(data)
        except json.JSONDecodeError as e:
            return json.dumps({"error": f"Invalid JSON: {str(e)}", "user_message": "Invalid data format."})
        
        if is_user_scoped:
            result = client.schema("api").table('tasks').update(update_data).eq('id', task_id).execute()
        else:
            result = client.execute_query(lambda: client.table('tasks').update(update_data).eq('id', task_id).execute())
        
        if not result.data:
            return json.dumps({"error": "Task not found", "user_message": "Could not find the task to update."})
        
        logger.info(f"Successfully updated task {task_id} for user {user_id}")
        return json.dumps({"success": True, "data": result.data[0] if result.data else None, "message": "Successfully updated task"})
        
    except AuthenticationError as e:
        return json.dumps({"error": e.message, "code": e.code, "user_message": e.user_message})
    except (SupabaseQueryError, Exception) as e:
        logger.error(f"Error updating task: {str(e)}")
        return json.dumps({"error": str(e), "user_message": "Failed to update task."})


@tool
def delete_task(user_id: str, task_id: str, confirm: bool = False, user_jwt: Optional[str] = None) -> str:
    """Delete a task from Supabase."""
    try:
        if not user_id:
            return json.dumps({"error": "user_id is required", "user_message": "User identification is required."})
        if not confirm:
            return json.dumps({"error": "Deletion not confirmed", "user_message": "Please confirm deletion."})
        
        client, is_user_scoped = get_supabase_client_for_operation(user_id, user_jwt)
        
        if is_user_scoped:
            result = client.schema("api").table('tasks').delete().eq('id', task_id).execute()
        else:
            result = client.execute_query(lambda: client.table('tasks').delete().eq('id', task_id).execute())
        
        if not result.data:
            return json.dumps({"error": "Task not found", "user_message": "Could not find the task to delete."})
        
        logger.info(f"Successfully deleted task {task_id} for user {user_id}")
        return json.dumps({"success": True, "message": "Successfully deleted task"})
        
    except AuthenticationError as e:
        return json.dumps({"error": e.message, "code": e.code, "user_message": e.user_message})
    except (SupabaseQueryError, Exception) as e:
        logger.error(f"Error deleting task: {str(e)}")
        return json.dumps({"error": str(e), "user_message": "Failed to delete task."})
