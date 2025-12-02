"""
Supabase tools for project operations.

This module provides specialized tools for project management including
get, create, update, and delete operations on the projects table.

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
    """Raised when authentication fails for agent tool operations."""
    
    def __init__(self, message: str, code: str):
        self.message = message
        self.code = code
        self.user_message = self._get_user_message(code)
        super().__init__(self.message)
        
    def _get_user_message(self, code: str) -> str:
        messages = {
            "MISSING_TOKEN": "Authentication required. Please log in.",
            "MISSING_USER_ID": "User identification required.",
        }
        return messages.get(code, "Authentication error. Please try again.")


def _get_supabase_client_for_operation(user_id: str, user_jwt: Optional[str] = None):
    """
    Get the appropriate Supabase client based on environment and JWT availability.
    """
    environment = os.getenv("ENVIRONMENT", "development")
    supabase_wrapper = get_supabase_client()
    
    if user_jwt:
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
            logger.warning("Falling back to service key client in development mode")
    
    if environment == "production":
        raise AuthenticationError("JWT required in production environment", "MISSING_TOKEN")
    
    logger.warning(f"Using service key - RLS bypassed (development mode) for user {user_id}")
    return supabase_wrapper, False


@tool
def get_projects(
    user_id: str,
    user_jwt: Optional[str] = None,
    status: Optional[str] = None,
    client_id: Optional[str] = None,
    limit: int = 10
) -> str:
    """
    Fetch projects from Supabase for a specific user.
    RLS policies automatically filter by user_id when using user-scoped client.
    
    Args:
        user_id: User ID to fetch projects for (required)
        user_jwt: Optional JWT token for user-scoped client creation
        status: Optional status filter (planning, in_progress, completed, on_hold, cancelled)
        client_id: Optional client ID filter
        limit: Maximum number of projects to return (default 10, max 100)
    
    Returns:
        JSON string of projects with details
    """
    try:
        if not user_id:
            return json.dumps({
                "error": "user_id is required",
                "user_message": "User identification is required to fetch projects."
            })
        
        client, is_user_scoped = _get_supabase_client_for_operation(user_id, user_jwt)
        limit = min(limit, 100)
        
        if is_user_scoped:
            query = client.schema("api").table('projects').select('*')
        else:
            query = client.table('projects').select('*')
        
        if status:
            query = query.eq('status', status)
        if client_id:
            query = query.eq('client_id', client_id)
        
        query = query.order('created_at', desc=True).limit(limit)
        
        if is_user_scoped:
            result = query.execute()
        else:
            result = client.execute_query(lambda: query.execute())
        
        logger.info(f"Successfully fetched {len(result.data)} projects for user {user_id}")
        
        return json.dumps({
            "success": True,
            "data": result.data,
            "count": len(result.data)
        })
        
    except AuthenticationError as e:
        logger.error(f"Authentication error fetching projects: {str(e)}")
        return json.dumps({"error": e.message, "code": e.code, "user_message": e.user_message})
    except SupabaseQueryError as e:
        logger.error(f"Failed to fetch projects: {str(e)}")
        return json.dumps({"error": str(e), "user_message": "Failed to retrieve projects. Please try again."})
    except Exception as e:
        logger.error(f"Unexpected error fetching projects: {str(e)}")
        return json.dumps({"error": str(e), "user_message": "An unexpected error occurred while fetching projects."})


@tool
def create_project(
    user_id: str,
    data: str,
    user_jwt: Optional[str] = None
) -> str:
    """
    Create a new project in Supabase for a specific user.
    
    Args:
        user_id: User ID creating the project (required)
        data: JSON string containing project data. Required fields:
            - name: Project name
            - client_name: Name of the client
            Optional fields:
            - client_id, description, start_date, end_date, budget, status, notes
        user_jwt: Optional JWT token for user-scoped client creation
    
    Returns:
        JSON string with created project or error message
    """
    try:
        if not user_id:
            return json.dumps({
                "error": "user_id is required",
                "user_message": "User identification is required to create a project."
            })
        
        client, is_user_scoped = _get_supabase_client_for_operation(user_id, user_jwt)
        
        try:
            project_data = json.loads(data)
        except json.JSONDecodeError as e:
            return json.dumps({
                "error": f"Invalid JSON: {str(e)}",
                "user_message": "The project data format is invalid. Please provide valid JSON."
            })
        
        required_fields = ['name', 'client_name']
        missing_fields = [f for f in required_fields if f not in project_data]
        if missing_fields:
            return json.dumps({
                "error": f"Missing required fields: {', '.join(missing_fields)}",
                "user_message": f"Please provide the following required fields: {', '.join(missing_fields)}"
            })
        
        if 'status' not in project_data:
            project_data['status'] = 'planning'
        
        project_data['user_id'] = user_id
        
        if is_user_scoped:
            result = client.schema("api").table('projects').insert(project_data).execute()
        else:
            result = client.execute_query(
                lambda: client.table('projects').insert(project_data).execute()
            )
        
        logger.info(f"Successfully created project {project_data.get('name')} for user {user_id}")
        
        return json.dumps({
            "success": True,
            "data": result.data[0] if result.data else None,
            "message": "Successfully created project"
        })
        
    except AuthenticationError as e:
        logger.error(f"Authentication error creating project: {str(e)}")
        return json.dumps({"error": e.message, "code": e.code, "user_message": e.user_message})
    except SupabaseQueryError as e:
        logger.error(f"Failed to create project: {str(e)}")
        return json.dumps({"error": str(e), "user_message": "Failed to create project. Please check your data."})
    except Exception as e:
        logger.error(f"Unexpected error creating project: {str(e)}")
        return json.dumps({"error": str(e), "user_message": "An unexpected error occurred while creating the project."})


@tool
def update_project(
    user_id: str,
    project_id: str,
    data: str,
    user_jwt: Optional[str] = None
) -> str:
    """
    Update an existing project in Supabase.
    RLS policies ensure users can only update their own projects.
    
    Args:
        user_id: User ID performing the update (required)
        project_id: The UUID of the project to update
        data: JSON string containing fields to update
        user_jwt: Optional JWT token for user-scoped client creation
    
    Returns:
        JSON string with updated project or error message
    """
    try:
        if not user_id:
            return json.dumps({
                "error": "user_id is required",
                "user_message": "User identification is required to update a project."
            })
        
        client, is_user_scoped = _get_supabase_client_for_operation(user_id, user_jwt)
        
        try:
            update_data = json.loads(data)
        except json.JSONDecodeError as e:
            return json.dumps({
                "error": f"Invalid JSON: {str(e)}",
                "user_message": "The update data format is invalid. Please provide valid JSON."
            })
        
        if is_user_scoped:
            query = client.schema("api").table('projects').update(update_data).eq('id', project_id)
            result = query.execute()
        else:
            query = client.table('projects').update(update_data).eq('id', project_id)
            result = client.execute_query(lambda: query.execute())
        
        if not result.data:
            return json.dumps({
                "error": "Project not found or access denied",
                "user_message": "Could not find the project to update. Please check the project ID."
            })
        
        logger.info(f"Successfully updated project {project_id} for user {user_id}")
        
        return json.dumps({
            "success": True,
            "data": result.data[0] if result.data else None,
            "message": "Successfully updated project"
        })
        
    except AuthenticationError as e:
        logger.error(f"Authentication error updating project: {str(e)}")
        return json.dumps({"error": e.message, "code": e.code, "user_message": e.user_message})
    except SupabaseQueryError as e:
        logger.error(f"Failed to update project: {str(e)}")
        return json.dumps({"error": str(e), "user_message": "Failed to update project. Please try again."})
    except Exception as e:
        logger.error(f"Unexpected error updating project: {str(e)}")
        return json.dumps({"error": str(e), "user_message": "An unexpected error occurred while updating the project."})


@tool
def delete_project(
    user_id: str,
    project_id: str,
    confirm: bool = False,
    user_jwt: Optional[str] = None
) -> str:
    """
    Delete a project from Supabase.
    RLS policies ensure users can only delete their own projects.
    
    Args:
        user_id: User ID performing the deletion (required)
        project_id: The UUID of the project to delete
        confirm: Must be True to confirm deletion (safety check)
        user_jwt: Optional JWT token for user-scoped client creation
    
    Returns:
        JSON string with deletion result or error message
    """
    try:
        if not user_id:
            return json.dumps({
                "error": "user_id is required",
                "user_message": "User identification is required to delete a project."
            })
        
        if not confirm:
            return json.dumps({
                "error": "Deletion not confirmed",
                "user_message": "Please confirm that you want to delete this project. This action cannot be undone."
            })
        
        client, is_user_scoped = _get_supabase_client_for_operation(user_id, user_jwt)
        
        if is_user_scoped:
            query = client.schema("api").table('projects').delete().eq('id', project_id)
            result = query.execute()
        else:
            query = client.table('projects').delete().eq('id', project_id)
            result = client.execute_query(lambda: query.execute())
        
        if not result.data:
            return json.dumps({
                "error": "Project not found or access denied",
                "user_message": "Could not find the project to delete. Please check the project ID."
            })
        
        logger.info(f"Successfully deleted project {project_id} for user {user_id}")
        
        return json.dumps({
            "success": True,
            "message": "Successfully deleted project"
        })
        
    except AuthenticationError as e:
        logger.error(f"Authentication error deleting project: {str(e)}")
        return json.dumps({"error": e.message, "code": e.code, "user_message": e.user_message})
    except SupabaseQueryError as e:
        logger.error(f"Failed to delete project: {str(e)}")
        return json.dumps({"error": str(e), "user_message": "Failed to delete project. Please try again."})
    except Exception as e:
        logger.error(f"Unexpected error deleting project: {str(e)}")
        return json.dumps({"error": str(e), "user_message": "An unexpected error occurred while deleting the project."})
