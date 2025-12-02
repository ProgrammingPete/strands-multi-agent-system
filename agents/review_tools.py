"""
Supabase tools for review operations.

This module provides specialized tools for review management including
get, create, update, and delete operations on the reviews table.
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
def get_reviews(
    user_id: str,
    user_jwt: Optional[str] = None,
    rating: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 10
) -> str:
    """
    Fetch reviews from Supabase for a specific user.
    
    Args:
        user_id: User ID to fetch reviews for (required)
        user_jwt: Optional JWT token for user-scoped client creation
        rating: Optional rating filter (1-5)
        status: Optional status filter (pending, published, responded, hidden)
        limit: Maximum number of reviews to return (default 10, max 100)
    """
    try:
        if not user_id:
            return json.dumps({"error": "user_id is required", "user_message": "User identification is required."})
        
        client, is_user_scoped = get_supabase_client_for_operation(user_id, user_jwt)
        limit = min(limit, 100)
        
        if is_user_scoped:
            query = client.schema("api").table('reviews').select('*')
        else:
            query = client.table('reviews').select('*')
        
        if rating:
            query = query.eq('rating', rating)
        if status:
            query = query.eq('status', status)
        
        query = query.order('created_at', desc=True).limit(limit)
        result = query.execute() if is_user_scoped else client.execute_query(lambda: query.execute())
        
        logger.info(f"Successfully fetched {len(result.data)} reviews for user {user_id}")
        return json.dumps({"success": True, "data": result.data, "count": len(result.data)})
        
    except AuthenticationError as e:
        return json.dumps({"error": e.message, "code": e.code, "user_message": e.user_message})
    except (SupabaseQueryError, Exception) as e:
        logger.error(f"Error fetching reviews: {str(e)}")
        return json.dumps({"error": str(e), "user_message": "Failed to retrieve reviews."})


@tool
def create_review(user_id: str, data: str, user_jwt: Optional[str] = None) -> str:
    """Create a new review in Supabase for a specific user."""
    try:
        if not user_id:
            return json.dumps({"error": "user_id is required", "user_message": "User identification is required."})
        
        client, is_user_scoped = get_supabase_client_for_operation(user_id, user_jwt)
        
        try:
            review_data = json.loads(data)
        except json.JSONDecodeError as e:
            return json.dumps({"error": f"Invalid JSON: {str(e)}", "user_message": "Invalid data format."})
        
        required_fields = ['reviewer_name', 'rating']
        missing = [f for f in required_fields if f not in review_data]
        if missing:
            return json.dumps({"error": f"Missing: {', '.join(missing)}", "user_message": f"Please provide: {', '.join(missing)}"})
        
        review_data.setdefault('status', 'pending')
        review_data['user_id'] = user_id
        
        if is_user_scoped:
            result = client.schema("api").table('reviews').insert(review_data).execute()
        else:
            result = client.execute_query(lambda: client.table('reviews').insert(review_data).execute())
        
        logger.info(f"Successfully created review for user {user_id}")
        return json.dumps({"success": True, "data": result.data[0] if result.data else None, "message": "Successfully created review"})
        
    except AuthenticationError as e:
        return json.dumps({"error": e.message, "code": e.code, "user_message": e.user_message})
    except (SupabaseQueryError, Exception) as e:
        logger.error(f"Error creating review: {str(e)}")
        return json.dumps({"error": str(e), "user_message": "Failed to create review."})


@tool
def update_review(user_id: str, review_id: str, data: str, user_jwt: Optional[str] = None) -> str:
    """Update an existing review in Supabase."""
    try:
        if not user_id:
            return json.dumps({"error": "user_id is required", "user_message": "User identification is required."})
        
        client, is_user_scoped = get_supabase_client_for_operation(user_id, user_jwt)
        
        try:
            update_data = json.loads(data)
        except json.JSONDecodeError as e:
            return json.dumps({"error": f"Invalid JSON: {str(e)}", "user_message": "Invalid data format."})
        
        if is_user_scoped:
            result = client.schema("api").table('reviews').update(update_data).eq('id', review_id).execute()
        else:
            result = client.execute_query(lambda: client.table('reviews').update(update_data).eq('id', review_id).execute())
        
        if not result.data:
            return json.dumps({"error": "Review not found", "user_message": "Could not find the review to update."})
        
        logger.info(f"Successfully updated review {review_id} for user {user_id}")
        return json.dumps({"success": True, "data": result.data[0] if result.data else None, "message": "Successfully updated review"})
        
    except AuthenticationError as e:
        return json.dumps({"error": e.message, "code": e.code, "user_message": e.user_message})
    except (SupabaseQueryError, Exception) as e:
        logger.error(f"Error updating review: {str(e)}")
        return json.dumps({"error": str(e), "user_message": "Failed to update review."})


@tool
def delete_review(user_id: str, review_id: str, confirm: bool = False, user_jwt: Optional[str] = None) -> str:
    """Delete a review from Supabase."""
    try:
        if not user_id:
            return json.dumps({"error": "user_id is required", "user_message": "User identification is required."})
        if not confirm:
            return json.dumps({"error": "Deletion not confirmed", "user_message": "Please confirm deletion."})
        
        client, is_user_scoped = get_supabase_client_for_operation(user_id, user_jwt)
        
        if is_user_scoped:
            result = client.schema("api").table('reviews').delete().eq('id', review_id).execute()
        else:
            result = client.execute_query(lambda: client.table('reviews').delete().eq('id', review_id).execute())
        
        if not result.data:
            return json.dumps({"error": "Review not found", "user_message": "Could not find the review to delete."})
        
        logger.info(f"Successfully deleted review {review_id} for user {user_id}")
        return json.dumps({"success": True, "message": "Successfully deleted review"})
        
    except AuthenticationError as e:
        return json.dumps({"error": e.message, "code": e.code, "user_message": e.user_message})
    except (SupabaseQueryError, Exception) as e:
        logger.error(f"Error deleting review: {str(e)}")
        return json.dumps({"error": str(e), "user_message": "Failed to delete review."})
