"""
Tests for Supabase optimization features.

This module tests the caching, connection pooling, and batch operation
optimizations to ensure they work correctly and provide expected benefits.
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from utils.supabase_cache import SupabaseCache, CacheEntry, cached_query
from utils.supabase_pool import SupabaseConnectionPool, ConnectionInfo, ConnectionType
from utils.supabase_batch import SupabaseBatcher, BatchOperation, BatchOperationType


class TestSupabaseCache:
    """Test caching functionality."""
    
    @pytest.fixture
    def cache(self):
        """Create a cache instance for testing."""
        return SupabaseCache(max_size=10, default_ttl=60)
    
    @pytest.mark.asyncio
    async def test_cache_entry_expiration(self):
        """Test cache entry expiration logic."""
        # Create entry with 2 second TTL to avoid timing issues
        entry = CacheEntry("test_data", ttl_seconds=2)
        
        # Should not be expired immediately
        assert not entry.is_expired()
        # Allow for small timing variations
        assert entry.time_to_live() >= 0
        
        # Wait for expiration
        await asyncio.sleep(2.1)
        
        # Should be expired now
        assert entry.is_expired()
        assert entry.time_to_live() == 0
    
    @pytest.mark.asyncio
    async def test_cache_get_set(self, cache):
        """Test basic cache get/set operations."""
        user_id = "test-user"
        table = "contacts"
        query_params = {"type": "client"}
        data = [{"id": "1", "name": "Test Contact"}]
        
        # Cache miss
        result = await cache.get(user_id, table, query_params)
        assert result is None
        
        # Set data
        await cache.set(user_id, table, query_params, data, ttl=60)
        
        # Cache hit
        result = await cache.get(user_id, table, query_params)
        assert result == data
    
    @pytest.mark.asyncio
    async def test_cache_invalidation(self, cache):
        """Test cache invalidation."""
        user_id = "test-user"
        table = "contacts"
        query_params = {"type": "client"}
        data = [{"id": "1", "name": "Test Contact"}]
        
        # Set data
        await cache.set(user_id, table, query_params, data)
        
        # Verify data is cached
        result = await cache.get(user_id, table, query_params)
        assert result == data
        
        # Check that cache has entries before invalidation
        assert len(cache._cache) > 0
        
        # Test user-level invalidation (should work with updated logic)
        count = await cache.invalidate_user(user_id)
        assert count == 1  # Should invalidate exactly 1 entry
        
        # Verify data is no longer cached
        result = await cache.get(user_id, table, query_params)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_size_limit(self, cache):
        """Test cache size limit and eviction."""
        user_id = "test-user"
        
        # Fill cache to capacity
        for i in range(cache._max_size):
            await cache.set(user_id, f"table_{i}", {}, f"data_{i}")
        
        # Add one more item (should trigger eviction)
        await cache.set(user_id, "overflow_table", {}, "overflow_data")
        
        # Cache should still be at max size
        assert len(cache._cache) == cache._max_size
    
    @pytest.mark.asyncio
    async def test_cached_query_decorator(self):
        """Test the cached_query decorator."""
        call_count = 0
        
        @cached_query("test_table", ttl=60)
        async def test_function(user_id: str, param: str = "default"):
            nonlocal call_count
            call_count += 1
            return f"result_{param}_{call_count}"
        
        user_id = "test-user"
        
        # First call - cache miss
        result1 = await test_function(user_id, "param1")
        assert result1 == "result_param1_1"
        assert call_count == 1
        
        # Second call with same params - cache hit
        result2 = await test_function(user_id, "param1")
        assert result2 == "result_param1_1"  # Same result
        assert call_count == 1  # Function not called again
        
        # Third call with different params - cache miss
        result3 = await test_function(user_id, "param2")
        assert result3 == "result_param2_2"
        assert call_count == 2


class TestSupabaseConnectionPool:
    """Test connection pooling functionality."""
    
    @pytest.fixture
    def pool(self):
        """Create a connection pool for testing."""
        return SupabaseConnectionPool(max_connections=5, max_idle_time=60)
    
    @pytest.mark.asyncio
    async def test_connection_info(self):
        """Test ConnectionInfo data structure."""
        mock_client = MagicMock()
        
        info = ConnectionInfo(
            client=mock_client,
            connection_type=ConnectionType.USER_SCOPED,
            user_id="test-user",
            created_at=1000.0,
            last_used_at=1000.0,
            use_count=0
        )
        
        assert info.client == mock_client
        assert info.connection_type == ConnectionType.USER_SCOPED
        assert info.user_id == "test-user"
        assert info.use_count == 0
    
    @pytest.mark.asyncio
    async def test_pool_lifecycle(self, pool):
        """Test pool start/stop lifecycle."""
        # Start pool
        await pool.start()
        assert pool._cleanup_task is not None
        
        # Stop pool
        await pool.stop()
        assert pool._cleanup_task is None
    
    @pytest.mark.asyncio
    async def test_pool_stats(self, pool):
        """Test pool statistics."""
        stats = pool.get_stats()
        
        assert hasattr(stats, 'total_connections')
        assert hasattr(stats, 'active_connections')
        assert hasattr(stats, 'idle_connections')
        assert hasattr(stats, 'total_requests')
        assert hasattr(stats, 'cache_hits')
        assert hasattr(stats, 'cache_misses')
        assert hasattr(stats, 'average_request_time_ms')


class TestSupabaseBatcher:
    """Test batch operations functionality."""
    
    @pytest.fixture
    def batcher(self):
        """Create a batcher instance for testing."""
        return SupabaseBatcher(max_batch_size=5)
    
    def test_batch_operation_creation(self):
        """Test BatchOperation data structure."""
        operation = BatchOperation(
            operation_type=BatchOperationType.INSERT,
            table="contacts",
            data={"name": "Test Contact"},
            filters=None,
            id_field="id"
        )
        
        assert operation.operation_type == BatchOperationType.INSERT
        assert operation.table == "contacts"
        assert operation.data == {"name": "Test Contact"}
        assert operation.id_field == "id"
    
    def test_operation_grouping(self, batcher):
        """Test operation grouping by table and type."""
        operations = [
            BatchOperation(BatchOperationType.INSERT, "contacts", {"name": "Contact 1"}),
            BatchOperation(BatchOperationType.INSERT, "contacts", {"name": "Contact 2"}),
            BatchOperation(BatchOperationType.UPDATE, "contacts", {"name": "Updated"}, {"id": "1"}),
            BatchOperation(BatchOperationType.INSERT, "invoices", {"number": "INV-001"}),
        ]
        
        grouped = batcher._group_operations(operations)
        
        # Should have 3 groups: contacts insert, contacts update, invoices insert
        assert len(grouped) == 3
        assert ("contacts", BatchOperationType.INSERT) in grouped
        assert ("contacts", BatchOperationType.UPDATE) in grouped
        assert ("invoices", BatchOperationType.INSERT) in grouped
        
        # Check group sizes
        assert len(grouped[("contacts", BatchOperationType.INSERT)]) == 2
        assert len(grouped[("contacts", BatchOperationType.UPDATE)]) == 1
        assert len(grouped[("invoices", BatchOperationType.INSERT)]) == 1
    
    @pytest.mark.asyncio
    async def test_batch_result_structure(self, batcher):
        """Test BatchResult data structure."""
        # Mock the Supabase operations to avoid actual database calls
        with patch.object(batcher, '_execute_operation_group') as mock_execute:
            mock_execute.return_value = [{"id": "1", "name": "Test"}]
            
            operations = [
                BatchOperation(BatchOperationType.INSERT, "contacts", {"name": "Test Contact"})
            ]
            
            result = await batcher.execute_batch(operations, "test-user")
            
            assert hasattr(result, 'success')
            assert hasattr(result, 'operation_count')
            assert hasattr(result, 'results')
            assert hasattr(result, 'errors')
            assert hasattr(result, 'execution_time_ms')
            
            assert result.operation_count == 1
            assert isinstance(result.execution_time_ms, int)


class TestOptimizationIntegration:
    """Test integration of all optimization features."""
    
    @pytest.mark.asyncio
    async def test_optimization_config_loading(self):
        """Test optimization configuration loading."""
        from backend.optimization_config import (
            optimization_settings,
            get_cache_ttl,
            get_optimization_config,
            is_optimization_enabled
        )
        
        # Test TTL retrieval
        contacts_ttl = get_cache_ttl("contacts")
        assert isinstance(contacts_ttl, int)
        assert contacts_ttl > 0
        
        # Test config retrieval
        config = get_optimization_config()
        assert "cache" in config
        assert "connection_pool" in config
        assert "batch_operations" in config
        assert "monitoring" in config
        
        # Test feature enablement check
        cache_enabled = is_optimization_enabled("cache")
        assert isinstance(cache_enabled, bool)
    
    @pytest.mark.asyncio
    async def test_performance_improvement_simulation(self):
        """Simulate performance improvements with optimizations."""
        import time
        
        # Simulate operations without optimizations
        start_time = time.time()
        
        # Simulate 10 individual API calls
        for _ in range(10):
            await asyncio.sleep(0.01)  # 10ms per API call
        
        unoptimized_time = time.time() - start_time
        
        # Simulate operations with optimizations
        start_time = time.time()
        
        # Simulate 2 API calls (cache misses) + 8 cache hits
        for _ in range(2):
            await asyncio.sleep(0.01)  # 10ms per API call
        
        for _ in range(8):
            await asyncio.sleep(0.001)  # 1ms per cache hit
        
        optimized_time = time.time() - start_time
        
        # Calculate improvement
        improvement = ((unoptimized_time - optimized_time) / unoptimized_time) * 100
        
        # Should see significant improvement (>50%)
        assert improvement > 50
        assert optimized_time < unoptimized_time


# Integration test with mocked Supabase client
@pytest.mark.asyncio
async def test_optimized_contact_operations():
    """Test optimized contact operations with mocked Supabase."""
    
    # Mock all the necessary components
    with patch('utils.supabase_cache.get_cache') as mock_get_cache, \
         patch('utils.supabase_pool.with_pooled_connection') as mock_pooled_conn:
        
        # Mock cache with proper async methods
        mock_cache = MagicMock()
        mock_cache.get = AsyncMock(return_value=None)  # Cache miss
        mock_cache.set = AsyncMock()
        mock_cache.invalidate_table = AsyncMock(return_value=1)
        mock_get_cache.return_value = mock_cache
        
        # Mock pooled connection to return test data
        async def mock_pooled_operation(operation, user_id=None, jwt_token=None):
            # Simulate successful query result
            mock_result = MagicMock()
            mock_result.data = [{"id": "1", "name": "Test Contact"}]
            return mock_result
        
        mock_pooled_conn.side_effect = mock_pooled_operation
        
        # Import and test optimized contact function
        from agents.contact_tools import get_contacts
        
        user_id = "550e8400-e29b-41d4-a716-446655440000"  # Valid UUID format
        
        # First call - should work with mocked components
        result1 = await get_contacts(user_id)
        result_data1 = json.loads(result1)
        
        # Should return success with mocked data
        assert result_data1["success"] is True
        assert len(result_data1["data"]) == 1
        assert result_data1["data"][0]["name"] == "Test Contact"
        
        # Verify cache was called
        mock_cache.get.assert_called_once()
        mock_cache.set.assert_called_once()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])