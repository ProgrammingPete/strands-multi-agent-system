"""
Supabase caching layer for frequently accessed data.

This module provides caching functionality to reduce Supabase API calls
for frequently accessed, relatively static data like user profiles,
contact lists, and configuration data.
"""

import logging
import asyncio
import json
from typing import Optional, Dict, Any, List, Callable, TypeVar
from datetime import datetime, timedelta
from functools import wraps
import hashlib

logger = logging.getLogger(__name__)

T = TypeVar('T')

class CacheEntry:
    """Represents a cached entry with expiration."""
    
    def __init__(self, data: Any, ttl_seconds: int, user_id: str = None, table: str = None):
        self.data = data
        self.created_at = datetime.now()
        self.expires_at = self.created_at + timedelta(seconds=ttl_seconds)
        self.user_id = user_id
        self.table = table
    
    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        return datetime.now() > self.expires_at
    
    def time_to_live(self) -> int:
        """Get remaining TTL in seconds."""
        remaining = (self.expires_at - datetime.now()).total_seconds()
        return max(0, int(remaining))


class SupabaseCache:
    """
    In-memory cache for Supabase query results.
    
    Features:
    - TTL-based expiration
    - User-scoped caching (respects RLS)
    - Cache invalidation by patterns
    - Memory-efficient with size limits
    - Thread-safe operations
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        Initialize the cache.
        
        Args:
            max_size: Maximum number of cache entries
            default_ttl: Default TTL in seconds (5 minutes)
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._lock = asyncio.Lock()
        logger.info(f"SupabaseCache initialized: max_size={max_size}, default_ttl={default_ttl}s")
    
    def _generate_key(self, user_id: str, table: str, query_params: Dict[str, Any]) -> str:
        """
        Generate a cache key from user_id, table, and query parameters.
        
        Args:
            user_id: User ID for scoping
            table: Table name
            query_params: Query parameters (filters, limits, etc.)
            
        Returns:
            Cache key string
        """
        # Sort params for consistent key generation
        sorted_params = json.dumps(query_params, sort_keys=True)
        key_data = f"{user_id}:{table}:{sorted_params}"
        
        # Hash for consistent length and avoid special characters
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def get(self, user_id: str, table: str, query_params: Dict[str, Any]) -> Optional[Any]:
        """
        Get cached data if available and not expired.
        
        Args:
            user_id: User ID for scoping
            table: Table name
            query_params: Query parameters
            
        Returns:
            Cached data or None if not found/expired
        """
        key = self._generate_key(user_id, table, query_params)
        
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            
            if entry.is_expired():
                del self._cache[key]
                logger.debug(f"Cache entry expired and removed: {key}")
                return None
            
            logger.debug(f"Cache hit: {key} (TTL: {entry.time_to_live()}s)")
            return entry.data
    
    async def set(
        self,
        user_id: str,
        table: str,
        query_params: Dict[str, Any],
        data: Any,
        ttl: Optional[int] = None
    ) -> None:
        """
        Store data in cache with TTL.
        
        Args:
            user_id: User ID for scoping
            table: Table name
            query_params: Query parameters
            data: Data to cache
            ttl: TTL in seconds (uses default if None)
        """
        key = self._generate_key(user_id, table, query_params)
        ttl = ttl or self._default_ttl
        
        async with self._lock:
            # Evict oldest entries if at capacity
            if len(self._cache) >= self._max_size:
                await self._evict_oldest()
            
            self._cache[key] = CacheEntry(data, ttl, user_id, table)
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
    
    async def invalidate_user(self, user_id: str) -> int:
        """
        Invalidate all cache entries for a specific user.
        
        Args:
            user_id: User ID to invalidate
            
        Returns:
            Number of entries invalidated
        """
        async with self._lock:
            keys_to_remove = [
                key for key, entry in self._cache.items()
                if entry.user_id == user_id
            ]
            
            for key in keys_to_remove:
                del self._cache[key]
            
            count = len(keys_to_remove)
            logger.info(f"Invalidated {count} cache entries for user {user_id}")
            return count
    
    async def invalidate_table(self, user_id: str, table: str) -> int:
        """
        Invalidate all cache entries for a specific user and table.
        
        Args:
            user_id: User ID
            table: Table name
            
        Returns:
            Number of entries invalidated
        """
        async with self._lock:
            keys_to_remove = [
                key for key, entry in self._cache.items()
                if entry.user_id == user_id and entry.table == table
            ]
            
            for key in keys_to_remove:
                del self._cache[key]
            
            count = len(keys_to_remove)
            logger.info(f"Invalidated {count} cache entries for user {user_id}, table {table}")
            return count
    
    async def _evict_oldest(self) -> None:
        """Evict the oldest cache entry."""
        if not self._cache:
            return
        
        # Find oldest entry by creation time
        oldest_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].created_at
        )
        
        del self._cache[oldest_key]
        logger.debug(f"Evicted oldest cache entry: {oldest_key}")
    
    async def cleanup_expired(self) -> int:
        """
        Remove all expired entries from cache.
        
        Returns:
            Number of entries removed
        """
        async with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            count = len(expired_keys)
            if count > 0:
                logger.info(f"Cleaned up {count} expired cache entries")
            return count
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        total_entries = len(self._cache)
        expired_count = sum(1 for entry in self._cache.values() if entry.is_expired())
        
        return {
            "total_entries": total_entries,
            "expired_entries": expired_count,
            "active_entries": total_entries - expired_count,
            "max_size": self._max_size,
            "utilization": total_entries / self._max_size if self._max_size > 0 else 0
        }


# Global cache instance
_cache_instance: Optional[SupabaseCache] = None


def get_cache() -> SupabaseCache:
    """Get the global cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = SupabaseCache()
    return _cache_instance


def cached_query(
    table: str,
    ttl: int = 300,
    cache_on_empty: bool = False
):
    """
    Decorator to cache Supabase query results.
    
    Args:
        table: Table name for cache scoping
        ttl: TTL in seconds
        cache_on_empty: Whether to cache empty results
        
    Usage:
        @cached_query("contacts", ttl=600)
        async def get_contacts(user_id: str, contact_type: str = None):
            # Query implementation
            pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # Extract user_id from arguments
            user_id = kwargs.get('user_id') or (args[0] if args else None)
            if not user_id:
                # No user_id, skip caching
                return await func(*args, **kwargs)
            
            # Build cache key from function arguments
            cache_params = {
                'function': func.__name__,
                'args': args[1:],  # Skip user_id
                'kwargs': {k: v for k, v in kwargs.items() if k != 'user_id'}
            }
            
            cache = get_cache()
            
            # Try to get from cache
            cached_result = await cache.get(user_id, table, cache_params)
            if cached_result is not None:
                return cached_result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result if not empty or if caching empty results is enabled
            if result or cache_on_empty:
                await cache.set(user_id, table, cache_params, result, ttl)
            
            return result
        
        return wrapper
    return decorator


# Cache cleanup task
async def start_cache_cleanup_task():
    """Start background task to clean up expired cache entries."""
    async def cleanup_loop():
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                cache = get_cache()
                await cache.cleanup_expired()
            except Exception as e:
                logger.error(f"Error in cache cleanup task: {e}")
    
    asyncio.create_task(cleanup_loop())
    logger.info("Started cache cleanup background task")