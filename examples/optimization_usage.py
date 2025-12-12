"""
Example usage of Supabase optimization features.

This script demonstrates how to use the caching, batching, and connection pooling
optimizations to reduce Supabase API calls and improve performance.
"""

import asyncio
import json
import logging
import sys
import os
from typing import List, Dict, Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import optimization utilities
from utils.supabase_cache import get_cache, cached_query
from utils.supabase_batch import batch_insert_records, batch_delete_records
from utils.supabase_pool import with_pooled_connection, get_connection_pool


async def example_caching():
    """Demonstrate caching functionality."""
    logger.info("=== Caching Example ===")
    
    cache = get_cache()
    user_id = "example-user-123"
    
    # Example: Cache frequently accessed contact list
    @cached_query("contacts", ttl=300)  # Cache for 5 minutes
    async def get_user_contacts(user_id: str, contact_type: str = None):
        """Simulated contact fetch with caching."""
        logger.info(f"Fetching contacts from database for user {user_id}")
        
        # Simulate database query
        await asyncio.sleep(0.1)  # Simulate network delay
        
        return [
            {"id": "1", "name": "John Doe", "type": contact_type or "client"},
            {"id": "2", "name": "Jane Smith", "type": contact_type or "client"}
        ]
    
    # First call - cache miss (will fetch from database)
    logger.info("First call (cache miss):")
    contacts1 = await get_user_contacts(user_id, "client")
    logger.info(f"Retrieved {len(contacts1)} contacts")
    
    # Second call - cache hit (will return from cache)
    logger.info("Second call (cache hit):")
    contacts2 = await get_user_contacts(user_id, "client")
    logger.info(f"Retrieved {len(contacts2)} contacts")
    
    # Show cache statistics
    stats = cache.get_stats()
    logger.info(f"Cache stats: {stats}")
    
    # Invalidate cache for user
    await cache.invalidate_user(user_id)
    logger.info("Cache invalidated for user")


async def example_batching():
    """Demonstrate batch operations."""
    logger.info("\n=== Batching Example ===")
    
    user_id = "example-user-123"
    
    # Example: Batch insert multiple contacts
    contacts_to_create = [
        {
            "name": "Alice Johnson",
            "email": "alice@example.com",
            "contact_type": "client",
            "phone": "555-0101"
        },
        {
            "name": "Bob Wilson",
            "email": "bob@example.com", 
            "contact_type": "supplier",
            "phone": "555-0102"
        },
        {
            "name": "Carol Brown",
            "email": "carol@example.com",
            "contact_type": "client",
            "phone": "555-0103"
        }
    ]
    
    logger.info(f"Batch creating {len(contacts_to_create)} contacts")
    
    # Note: This would normally connect to Supabase
    # For demo purposes, we'll simulate the batch operation
    try:
        # result = await batch_insert_records("contacts", contacts_to_create, user_id)
        # logger.info(f"Batch insert completed in {result.execution_time_ms}ms")
        # logger.info(f"Created {len(result.results)} contacts")
        
        logger.info("Batch insert simulation completed")
        
        # Example: Batch delete contacts
        contact_ids = ["contact-1", "contact-2", "contact-3"]
        logger.info(f"Batch deleting {len(contact_ids)} contacts")
        
        # result = await batch_delete_records("contacts", contact_ids, user_id)
        # logger.info(f"Batch delete completed in {result.execution_time_ms}ms")
        
        logger.info("Batch delete simulation completed")
        
    except Exception as e:
        logger.error(f"Batch operation failed: {e}")


async def example_connection_pooling():
    """Demonstrate connection pooling."""
    logger.info("\n=== Connection Pooling Example ===")
    
    user_id = "example-user-123"
    
    # Example: Multiple operations using pooled connections
    async def fetch_user_data(client):
        """Simulated database operation."""
        logger.info("Executing database query with pooled connection")
        await asyncio.sleep(0.05)  # Simulate query time
        return {"user_id": user_id, "data": "example"}
    
    # Execute multiple operations
    tasks = []
    for i in range(5):
        task = with_pooled_connection(fetch_user_data, user_id)
        tasks.append(task)
    
    logger.info("Executing 5 concurrent operations with connection pooling")
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    logger.info(f"Completed {len(results)} operations")
    
    # Show connection pool statistics
    pool = get_connection_pool()
    stats = pool.get_stats()
    logger.info(f"Pool stats: Total connections: {stats.total_connections}")
    logger.info(f"Pool stats: Active connections: {stats.active_connections}")
    logger.info(f"Pool stats: Cache hit rate: {stats.cache_hits}/{stats.total_requests}")


async def example_performance_comparison():
    """Demonstrate performance improvements."""
    logger.info("\n=== Performance Comparison ===")
    
    # Simulate operations without optimizations
    logger.info("Simulating operations WITHOUT optimizations:")
    
    start_time = asyncio.get_event_loop().time()
    
    # Simulate multiple individual API calls
    for i in range(10):
        await asyncio.sleep(0.02)  # Simulate API call latency
    
    unoptimized_time = asyncio.get_event_loop().time() - start_time
    logger.info(f"10 individual operations took {unoptimized_time:.3f} seconds")
    
    # Simulate operations with optimizations
    logger.info("Simulating operations WITH optimizations:")
    
    start_time = asyncio.get_event_loop().time()
    
    # Simulate cached responses (much faster)
    for i in range(8):  # 8 cache hits
        await asyncio.sleep(0.001)  # Cached response time
    
    # Simulate 2 actual API calls (cache misses)
    for i in range(2):
        await asyncio.sleep(0.02)  # API call latency
    
    optimized_time = asyncio.get_event_loop().time() - start_time
    logger.info(f"10 optimized operations took {optimized_time:.3f} seconds")
    
    improvement = ((unoptimized_time - optimized_time) / unoptimized_time) * 100
    logger.info(f"Performance improvement: {improvement:.1f}%")


async def main():
    """Run all optimization examples."""
    logger.info("Supabase Optimization Examples")
    logger.info("=" * 50)
    
    try:
        # Start connection pool for examples
        pool = get_connection_pool()
        await pool.start()
        
        # Run examples
        await example_caching()
        await example_batching()
        await example_connection_pooling()
        await example_performance_comparison()
        
        logger.info("\n=== Summary ===")
        logger.info("Optimization features demonstrated:")
        logger.info("✅ Caching - Reduces API calls for frequently accessed data")
        logger.info("✅ Batching - Combines multiple operations into single API calls")
        logger.info("✅ Connection Pooling - Reuses connections for better performance")
        logger.info("\nThese optimizations can significantly reduce Supabase traffic and costs!")
        
    except Exception as e:
        logger.error(f"Example failed: {e}")
    finally:
        # Cleanup
        pool = get_connection_pool()
        await pool.stop()


if __name__ == "__main__":
    asyncio.run(main())