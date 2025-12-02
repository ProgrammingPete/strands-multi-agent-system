"""
Supabase tools for appointment operations.

This module provides specialized tools for appointment management including
get, create, update, and delete operations on the appointments table.

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
def get_appointments(
    user_id: str,
    user_jwt: Optional[str] = None,
    status: Optional[str] = None,
    client_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 10
) -> str:
    """
    Fetch appointments from Supabase for a specific user.
    RLS policies automatically filter by user_id when using user-scoped client.
    
    Args:
        user_id: User ID to fetch appointments for (required)
        user_jwt: Optional JWT token for user-scoped client creation
        status: Optional status filter (scheduled, confirmed, completed, cancelled, no_show)
        client_id: Optional client ID filter
        start_date: Optional start date filter (YYYY-MM-DD)
        end_date: Optional end date filter (YYYY-MM-DD)
        limit: Maximum number of appointments to return (default 10, max 100)
    
    Returns:
        JSON string of appointments with details
    """
    try:
        if not user_id:
            return json.dumps({
                "error": "user_id is required",
                "user_message": "User identification is required to fetch appointments."
            })
        
        client, is_user_scoped = _get_supabase_client_for_operation(user_id, user_jwt)
        limit = min(limit, 100)
        
        if is_user_scoped:
            query = client.schema("api").table('appointments').select('*')
        else:
            query = client.table('appointments').select('*')
        
        if status:
            query = query.eq('status', status)
        if client_id:
            query = query.eq('client_id', client_id)
        if start_date:
            query = query.gte('scheduled_date', start_date)
        if end_date:
            query = query.lte('scheduled_date', end_date)
        
        query = query.order('scheduled_date', desc=False).limit(limit)
        
        if is_user_scoped:
            result = query.execute()
        else:
            result = client.execute_query(lambda: query.execute())
        
        logger.info(f"Successfully fetched {len(result.data)} appointments for user {user_id}")
        
        return json.dumps({
            "success": True,
            "data": result.data,
            "count": len(result.data)
        })
        
    except AuthenticationError as e:
        logger.error(f"Authentication error fetching appointments: {str(e)}")
        return json.dumps({"error": e.message, "code": e.code, "user_message": e.user_message})
    except SupabaseQueryError as e:
        logger.error(f"Failed to fetch appointments: {str(e)}")
        return json.dumps({"error": str(e), "user_message": "Failed to retrieve appointments. Please try again."})
    except Exception as e:
        logger.error(f"Unexpected error fetching appointments: {str(e)}")
        return json.dumps({"error": str(e), "user_message": "An unexpected error occurred while fetching appointments."})


@tool
def create_appointment(
    user_id: str,
    data: str,
    user_jwt: Optional[str] = None
) -> str:
    """
    Create a new appointment in Supabase for a specific user.
    
    Args:
        user_id: User ID creating the appointment (required)
        data: JSON string containing appointment data. Required fields:
            - client_name: Name of the client
            - scheduled_date: Date of appointment (YYYY-MM-DD)
            - scheduled_time: Time of appointment (HH:MM)
            Optional fields:
            - client_id, title, description, duration_minutes, location, status, notes
        user_jwt: Optional JWT token for user-scoped client creation
    
    Returns:
        JSON string with created appointment or error message
    """
    try:
        if not user_id:
            return json.dumps({
                "error": "user_id is required",
                "user_message": "User identification is required to create an appointment."
            })
        
        client, is_user_scoped = _get_supabase_client_for_operation(user_id, user_jwt)
        
        try:
            appointment_data = json.loads(data)
        except json.JSONDecodeError as e:
            return json.dumps({
                "error": f"Invalid JSON: {str(e)}",
                "user_message": "The appointment data format is invalid. Please provide valid JSON."
            })
        
        required_fields = ['client_name', 'scheduled_date', 'scheduled_time']
        missing_fields = [f for f in required_fields if f not in appointment_data]
        if missing_fields:
            return json.dumps({
                "error": f"Missing required fields: {', '.join(missing_fields)}",
                "user_message": f"Please provide the following required fields: {', '.join(missing_fields)}"
            })
        
        if 'status' not in appointment_data:
            appointment_data['status'] = 'scheduled'
        
        appointment_data['user_id'] = user_id
        
        if is_user_scoped:
            result = client.schema("api").table('appointments').insert(appointment_data).execute()
        else:
            result = client.execute_query(
                lambda: client.table('appointments').insert(appointment_data).execute()
            )
        
        logger.info(f"Successfully created appointment for user {user_id}")
        
        return json.dumps({
            "success": True,
            "data": result.data[0] if result.data else None,
            "message": "Successfully created appointment"
        })
        
    except AuthenticationError as e:
        logger.error(f"Authentication error creating appointment: {str(e)}")
        return json.dumps({"error": e.message, "code": e.code, "user_message": e.user_message})
    except SupabaseQueryError as e:
        logger.error(f"Failed to create appointment: {str(e)}")
        return json.dumps({"error": str(e), "user_message": "Failed to create appointment. Please check your data."})
    except Exception as e:
        logger.error(f"Unexpected error creating appointment: {str(e)}")
        return json.dumps({"error": str(e), "user_message": "An unexpected error occurred while creating the appointment."})


@tool
def update_appointment(
    user_id: str,
    appointment_id: str,
    data: str,
    user_jwt: Optional[str] = None
) -> str:
    """
    Update an existing appointment in Supabase.
    RLS policies ensure users can only update their own appointments.
    
    Args:
        user_id: User ID performing the update (required)
        appointment_id: The UUID of the appointment to update
        data: JSON string containing fields to update
        user_jwt: Optional JWT token for user-scoped client creation
    
    Returns:
        JSON string with updated appointment or error message
    """
    try:
        if not user_id:
            return json.dumps({
                "error": "user_id is required",
                "user_message": "User identification is required to update an appointment."
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
            query = client.schema("api").table('appointments').update(update_data).eq('id', appointment_id)
            result = query.execute()
        else:
            query = client.table('appointments').update(update_data).eq('id', appointment_id)
            result = client.execute_query(lambda: query.execute())
        
        if not result.data:
            return json.dumps({
                "error": "Appointment not found or access denied",
                "user_message": "Could not find the appointment to update. Please check the appointment ID."
            })
        
        logger.info(f"Successfully updated appointment {appointment_id} for user {user_id}")
        
        return json.dumps({
            "success": True,
            "data": result.data[0] if result.data else None,
            "message": "Successfully updated appointment"
        })
        
    except AuthenticationError as e:
        logger.error(f"Authentication error updating appointment: {str(e)}")
        return json.dumps({"error": e.message, "code": e.code, "user_message": e.user_message})
    except SupabaseQueryError as e:
        logger.error(f"Failed to update appointment: {str(e)}")
        return json.dumps({"error": str(e), "user_message": "Failed to update appointment. Please try again."})
    except Exception as e:
        logger.error(f"Unexpected error updating appointment: {str(e)}")
        return json.dumps({"error": str(e), "user_message": "An unexpected error occurred while updating the appointment."})


@tool
def delete_appointment(
    user_id: str,
    appointment_id: str,
    confirm: bool = False,
    user_jwt: Optional[str] = None
) -> str:
    """
    Delete an appointment from Supabase.
    RLS policies ensure users can only delete their own appointments.
    
    Args:
        user_id: User ID performing the deletion (required)
        appointment_id: The UUID of the appointment to delete
        confirm: Must be True to confirm deletion (safety check)
        user_jwt: Optional JWT token for user-scoped client creation
    
    Returns:
        JSON string with deletion result or error message
    """
    try:
        if not user_id:
            return json.dumps({
                "error": "user_id is required",
                "user_message": "User identification is required to delete an appointment."
            })
        
        if not confirm:
            return json.dumps({
                "error": "Deletion not confirmed",
                "user_message": "Please confirm that you want to delete this appointment. This action cannot be undone."
            })
        
        client, is_user_scoped = _get_supabase_client_for_operation(user_id, user_jwt)
        
        if is_user_scoped:
            query = client.schema("api").table('appointments').delete().eq('id', appointment_id)
            result = query.execute()
        else:
            query = client.table('appointments').delete().eq('id', appointment_id)
            result = client.execute_query(lambda: query.execute())
        
        if not result.data:
            return json.dumps({
                "error": "Appointment not found or access denied",
                "user_message": "Could not find the appointment to delete. Please check the appointment ID."
            })
        
        logger.info(f"Successfully deleted appointment {appointment_id} for user {user_id}")
        
        return json.dumps({
            "success": True,
            "message": "Successfully deleted appointment"
        })
        
    except AuthenticationError as e:
        logger.error(f"Authentication error deleting appointment: {str(e)}")
        return json.dumps({"error": e.message, "code": e.code, "user_message": e.user_message})
    except SupabaseQueryError as e:
        logger.error(f"Failed to delete appointment: {str(e)}")
        return json.dumps({"error": str(e), "user_message": "Failed to delete appointment. Please try again."})
    except Exception as e:
        logger.error(f"Unexpected error deleting appointment: {str(e)}")
        return json.dumps({"error": str(e), "user_message": "An unexpected error occurred while deleting the appointment."})
