"""
Enhanced connection pooling for Supabase operations.

This module provides improved connection management and pooling
to reduce connection overhead and improve performance.
"""

import logging
import asyncio
from typing import Optional, Dict, Any, List, Callable, TypeVar
from contextlib import asynccontextmanager
import time
from dataclasses import dataclass
from enum import Enum

from utils.supabase_client import get_supabase_client, SupabaseClientWrapper
from supabase import Client

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ConnectionType(Enum):
    """Types of connections in the pool."""
    SERVICE_KEY = "service_key"
    USER_SCOPED = "user_scoped"


@dataclass
class PoolStats:
    """Statistics for connection pool usage."""
    total_connections: int
    active_connections: int
    idle_connections: int
    total_requests: int
    cache_hits: int
    cache_misses: int
    average_request_time_ms: float


@dataclass
class ConnectionInfo:
    """Information about a pooled connection."""
    client: Client
    connection_type: ConnectionType
    user_id: Optional[str]
    created_at: float
    last_used_at: float
    use_count: int


class SupabaseConnectionPool:
    """
    Enhanced connection pool for Supabase operations.
    
    Features:
    - Connection reuse for user-scoped clients
    - Automatic cleanup of idle connections
    - Connection statistics and monitoring
    - Configurable pool size and timeouts
    """
    
    def __init__(
        self,
        max_connections: int = 50,
        max_idle_time: int = 300,  # 5 minutes
        cleanup_interval: int = 60   # 1 minute
    ):
        """
        Initialize the connection pool.
        
        Args:
            max_connections: Maximum number of connections to pool
            max_idle_time: Maximum idle time before connection cleanup (seconds)
            cleanup_interval: Interval between cleanup runs (seconds)
        """
        self.max_connections = max_connections
        self.max_idle_time = max_idle_time
        self.cleanup_interval = cleanup_interval
        
        # Connection pools by type
        self._service_connections: List[ConnectionInfo] = []
        self._user_connections: Dict[str, ConnectionInfo] = {}  # user_id -> connection
        
        # Statistics
        self._stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'request_times': []
        }
        
        # Synchronization
        self._lock = asyncio.Lock()
        
        # Background cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        
        logger.info(
            f"SupabaseConnectionPool initialized: "
            f"max_connections={max_connections}, "
            f"max_idle_time={max_idle_time}s, "
            f"cleanup_interval={cleanup_interval}s"
        )
    
    async def start(self):
        """Start the connection pool and background tasks."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("Connection pool cleanup task started")
    
    async def stop(self):
        """Stop the connection pool and cleanup resources."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
        
        async with self._lock:
            self._service_connections.clear()
            self._user_connections.clear()
        
        logger.info("Connection pool stopped")
    
    @asynccontextmanager
    async def get_connection(
        self,
        user_id: Optional[str] = None,
        jwt_token: Optional[str] = None
    ):
        """
        Get a connection from the pool.
        
        Args:
            user_id: User ID for user-scoped connections
            jwt_token: JWT token for user-scoped connections
            
        Yields:
            Supabase client instance
        """
        start_time = time.time()
        connection_info = None
        
        try:
            # Get connection from pool
            if jwt_token and user_id:
                connection_info = await self._get_user_connection(user_id, jwt_token)
            else:
                connection_info = await self._get_service_connection()
            
            # Update statistics
            self._stats['total_requests'] += 1
            if connection_info.use_count > 0:
                self._stats['cache_hits'] += 1
            else:
                self._stats['cache_misses'] += 1
            
            # Update connection usage
            connection_info.last_used_at = time.time()
            connection_info.use_count += 1
            
            yield connection_info.client
            
        finally:
            # Record request time
            request_time = (time.time() - start_time) * 1000
            self._stats['request_times'].append(request_time)
            
            # Keep only last 1000 request times for average calculation
            if len(self._stats['request_times']) > 1000:
                self._stats['request_times'] = self._stats['request_times'][-1000:]
    
    async def _get_user_connection(self, user_id: str, jwt_token: str) -> ConnectionInfo:
        """Get or create a user-scoped connection."""
        async with self._lock:
            # Check if we have a cached connection for this user
            if user_id in self._user_connections:
                connection_info = self._user_connections[user_id]
                
                # Check if connection is still valid (not too old)
                age = time.time() - connection_info.created_at
                if age < self.max_idle_time:
                    logger.debug(f"Reusing user connection for {user_id}")
                    return connection_info
                else:
                    # Connection too old, remove it
                    del self._user_connections[user_id]
                    logger.debug(f"Removed expired user connection for {user_id}")
            
            # Create new user-scoped connection
            supabase_wrapper = get_supabase_client()
            client = supabase_wrapper.create_user_scoped_client(jwt_token)
            
            connection_info = ConnectionInfo(
                client=client,
                connection_type=ConnectionType.USER_SCOPED,
                user_id=user_id,
                created_at=time.time(),
                last_used_at=time.time(),
                use_count=0
            )
            
            # Add to pool if we have space
            if len(self._user_connections) < self.max_connections:
                self._user_connections[user_id] = connection_info
                logger.debug(f"Created and cached user connection for {user_id}")
            else:
                logger.debug(f"Created user connection for {user_id} (not cached - pool full)")
            
            return connection_info
    
    async def _get_service_connection(self) -> ConnectionInfo:
        """Get or create a service key connection."""
        async with self._lock:
            # Try to reuse an existing service connection
            current_time = time.time()
            
            for connection_info in self._service_connections:
                age = current_time - connection_info.created_at
                if age < self.max_idle_time:
                    logger.debug("Reusing service connection")
                    return connection_info
            
            # Clean up old connections
            self._service_connections = [
                conn for conn in self._service_connections
                if (current_time - conn.created_at) < self.max_idle_time
            ]
            
            # Create new service connection
            supabase_wrapper = get_supabase_client()
            client = supabase_wrapper.client
            
            connection_info = ConnectionInfo(
                client=client,
                connection_type=ConnectionType.SERVICE_KEY,
                user_id=None,
                created_at=current_time,
                last_used_at=current_time,
                use_count=0
            )
            
            # Add to pool if we have space
            if len(self._service_connections) < self.max_connections // 2:  # Reserve half for service
                self._service_connections.append(connection_info)
                logger.debug("Created and cached service connection")
            else:
                logger.debug("Created service connection (not cached - pool full)")
            
            return connection_info
    
    async def _cleanup_loop(self):
        """Background task to cleanup idle connections."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_idle_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in connection pool cleanup: {e}")
    
    async def _cleanup_idle_connections(self):
        """Remove idle connections from the pool."""
        current_time = time.time()
        
        async with self._lock:
            # Cleanup service connections
            initial_service_count = len(self._service_connections)
            self._service_connections = [
                conn for conn in self._service_connections
                if (current_time - conn.last_used_at) < self.max_idle_time
            ]
            service_removed = initial_service_count - len(self._service_connections)
            
            # Cleanup user connections
            initial_user_count = len(self._user_connections)
            expired_users = [
                user_id for user_id, conn in self._user_connections.items()
                if (current_time - conn.last_used_at) >= self.max_idle_time
            ]
            
            for user_id in expired_users:
                del self._user_connections[user_id]
            
            user_removed = len(expired_users)
            
            if service_removed > 0 or user_removed > 0:
                logger.info(
                    f"Cleaned up {service_removed} service connections "
                    f"and {user_removed} user connections"
                )
    
    async def invalidate_user_connections(self, user_id: str):
        """
        Invalidate all connections for a specific user.
        
        Args:
            user_id: User ID to invalidate connections for
        """
        async with self._lock:
            if user_id in self._user_connections:
                del self._user_connections[user_id]
                logger.info(f"Invalidated connection for user {user_id}")
    
    def get_stats(self) -> PoolStats:
        """
        Get connection pool statistics.
        
        Returns:
            PoolStats with current pool statistics
        """
        current_time = time.time()
        
        # Count active vs idle connections
        active_service = sum(
            1 for conn in self._service_connections
            if (current_time - conn.last_used_at) < 60  # Active in last minute
        )
        
        active_user = sum(
            1 for conn in self._user_connections.values()
            if (current_time - conn.last_used_at) < 60  # Active in last minute
        )
        
        total_connections = len(self._service_connections) + len(self._user_connections)
        active_connections = active_service + active_user
        idle_connections = total_connections - active_connections
        
        # Calculate average request time
        avg_request_time = 0.0
        if self._stats['request_times']:
            avg_request_time = sum(self._stats['request_times']) / len(self._stats['request_times'])
        
        return PoolStats(
            total_connections=total_connections,
            active_connections=active_connections,
            idle_connections=idle_connections,
            total_requests=self._stats['total_requests'],
            cache_hits=self._stats['cache_hits'],
            cache_misses=self._stats['cache_misses'],
            average_request_time_ms=avg_request_time
        )


# Global connection pool instance
_pool_instance: Optional[SupabaseConnectionPool] = None


def get_connection_pool() -> SupabaseConnectionPool:
    """Get the global connection pool instance."""
    global _pool_instance
    if _pool_instance is None:
        _pool_instance = SupabaseConnectionPool()
    return _pool_instance


async def start_connection_pool():
    """Start the global connection pool."""
    pool = get_connection_pool()
    await pool.start()
    logger.info("Global connection pool started")


async def stop_connection_pool():
    """Stop the global connection pool."""
    global _pool_instance
    if _pool_instance:
        await _pool_instance.stop()
        _pool_instance = None
        logger.info("Global connection pool stopped")


# Convenience function for pooled operations
async def with_pooled_connection(
    operation: Callable[[Client], T],
    user_id: Optional[str] = None,
    jwt_token: Optional[str] = None
) -> T:
    """
    Execute an operation with a pooled connection.
    
    Args:
        operation: Function that takes a Supabase client and returns a result
        user_id: Optional user ID for user-scoped connections
        jwt_token: Optional JWT token for user-scoped connections
        
    Returns:
        Result of the operation
    """
    pool = get_connection_pool()
    
    async with pool.get_connection(user_id, jwt_token) as client:
        return await operation(client)