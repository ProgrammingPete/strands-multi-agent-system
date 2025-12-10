# Supabase Traffic Optimizations

This document describes the implemented optimizations to reduce Supabase API calls and improve performance in the Canvalo backend system.

## Overview

The backend now includes three key optimization strategies:

1. **Caching** - Reduces API calls for frequently accessed data
2. **Connection Pooling** - Reuses connections for better performance  
3. **Batch Operations** - Combines multiple operations into single API calls

These optimizations can significantly reduce Supabase traffic and associated costs while improving application performance.

## 1. Caching (`utils/supabase_cache.py`)

### Features
- **TTL-based expiration** - Configurable time-to-live for different data types
- **User-scoped caching** - Respects RLS by scoping cache entries to users
- **Automatic invalidation** - Cache entries are invalidated when data changes
- **Memory management** - Configurable size limits with LRU eviction
- **Background cleanup** - Automatic removal of expired entries

### Usage

#### Decorator-based Caching
```python
from utils.supabase_cache import cached_query

@tool
@cached_query("contacts", ttl=300)  # Cache for 5 minutes
async def get_contacts(user_id: str, contact_type: str = None):
    # Query implementation
    pass
```

#### Manual Cache Management
```python
from utils.supabase_cache import get_cache

cache = get_cache()

# Get cached data
result = await cache.get(user_id, "contacts", query_params)

# Store data in cache
await cache.set(user_id, "contacts", query_params, data, ttl=300)

# Invalidate cache
await cache.invalidate_table(user_id, "contacts")
```

### Configuration
Cache TTL can be configured per table type in `backend/optimization_config.py`:

```python
cache_ttl_contacts: int = 300      # 5 minutes
cache_ttl_invoices: int = 180      # 3 minutes  
cache_ttl_projects: int = 600      # 10 minutes
cache_ttl_appointments: int = 120  # 2 minutes
```

## 2. Connection Pooling (`utils/supabase_pool.py`)

### Features
- **Connection reuse** - Maintains pool of active connections
- **User-scoped connections** - Separate pools for service and user connections
- **Automatic cleanup** - Removes idle connections after timeout
- **Performance monitoring** - Tracks connection usage and performance
- **Configurable limits** - Max connections, idle timeouts, cleanup intervals

### Usage

#### Pooled Operations
```python
from utils.supabase_pool import with_pooled_connection

async def fetch_data(client):
    return client.schema("api").table("contacts").select("*").execute()

# Use pooled connection
result = await with_pooled_connection(fetch_data, user_id, jwt_token)
```

#### Context Manager
```python
from utils.supabase_pool import get_connection_pool

pool = get_connection_pool()

async with pool.get_connection(user_id, jwt_token) as client:
    result = client.schema("api").table("contacts").select("*").execute()
```

### Configuration
Pool settings in `backend/optimization_config.py`:

```python
pool_max_connections: int = 50      # Maximum pooled connections
pool_max_idle_time: int = 300       # 5 minutes idle timeout
pool_cleanup_interval: int = 60     # 1 minute cleanup interval
```

## 3. Batch Operations (`utils/supabase_batch.py`)

### Features
- **Bulk inserts** - Insert multiple records in single API call
- **Bulk updates** - Update multiple records efficiently
- **Bulk deletes** - Delete multiple records with IN clause
- **Error handling** - Partial success reporting and error details
- **Performance tracking** - Execution time monitoring

### Usage

#### Batch Insert
```python
from utils.supabase_batch import batch_insert_records

contacts = [
    {"name": "John Doe", "email": "john@example.com"},
    {"name": "Jane Smith", "email": "jane@example.com"}
]

result = await batch_insert_records("contacts", contacts, user_id, jwt_token)
```

#### Batch Delete
```python
from utils.supabase_batch import batch_delete_records

contact_ids = ["id1", "id2", "id3"]
result = await batch_delete_records("contacts", contact_ids, user_id, jwt_token)
```

#### Custom Batch Operations
```python
from utils.supabase_batch import get_batcher, BatchOperation, BatchOperationType

operations = [
    BatchOperation(
        operation_type=BatchOperationType.INSERT,
        table="contacts",
        data={"name": "New Contact"}
    )
]

batcher = get_batcher()
result = await batcher.execute_batch(operations, user_id, jwt_token)
```

## Integration with Existing Tools

### Updated Contact Tools
The contact tools have been updated to use all three optimizations:

```python
# Caching for read operations
@cached_query("contacts", ttl=300)
async def get_contacts(user_id: str, ...):
    # Uses connection pooling internally
    pass

# Cache invalidation for write operations  
async def create_contact(user_id: str, ...):
    # Create contact
    # Invalidate cache
    await get_cache().invalidate_table(user_id, "contacts")

# New batch operations
async def batch_create_contacts(user_id: str, contacts_data: str, ...):
    # Batch insert multiple contacts
    pass
```

## Performance Monitoring

### Optimization Statistics Endpoint
The backend exposes optimization statistics at `/api/optimization/stats`:

```json
{
  "cache": {
    "total_entries": 150,
    "active_entries": 120,
    "expired_entries": 30,
    "utilization_percent": 15.0,
    "max_size": 1000
  },
  "connection_pool": {
    "total_connections": 8,
    "active_connections": 3,
    "idle_connections": 5,
    "total_requests": 1250,
    "cache_hits": 1100,
    "cache_misses": 150,
    "hit_rate_percent": 88.0,
    "average_request_time_ms": 45.2
  }
}
```

### Logging
All optimization modules include detailed logging:

```
INFO - Cache hit: contacts query (TTL: 245s)
INFO - Connection pool: Reusing user connection for user-123
INFO - Batch insert completed: 25 records in 120ms
```

## Configuration

### Environment Variables
Optimization features can be configured via environment variables:

```bash
# Cache settings
OPTIMIZATION_CACHE_ENABLED=true
OPTIMIZATION_CACHE_MAX_SIZE=1000
OPTIMIZATION_CACHE_DEFAULT_TTL=300

# Connection pool settings  
OPTIMIZATION_POOL_ENABLED=true
OPTIMIZATION_POOL_MAX_CONNECTIONS=50
OPTIMIZATION_POOL_MAX_IDLE_TIME=300

# Batch operation settings
OPTIMIZATION_BATCH_ENABLED=true
OPTIMIZATION_BATCH_MAX_SIZE=100
```

### Runtime Configuration
Settings can be accessed and modified at runtime:

```python
from backend.optimization_config import optimization_settings, get_cache_ttl

# Get TTL for specific table
ttl = get_cache_ttl("contacts")  # Returns 300 seconds

# Check if feature is enabled
if optimization_settings.cache_enabled:
    # Use caching
    pass
```

## Performance Impact

### Expected Improvements
Based on typical usage patterns:

- **Cache hit rate**: 70-90% for frequently accessed data
- **API call reduction**: 50-80% for read operations
- **Response time improvement**: 60-90% for cached queries
- **Connection overhead reduction**: 40-60% with pooling
- **Bulk operation efficiency**: 80-95% fewer API calls for batch operations

### Example Scenarios

#### Scenario 1: Contact List Loading
- **Without optimization**: 10 individual API calls = 200ms
- **With caching**: 1 API call + 9 cache hits = 25ms
- **Improvement**: 87.5% faster

#### Scenario 2: Bulk Contact Import
- **Without optimization**: 50 individual inserts = 50 API calls
- **With batching**: 1 batch insert = 1 API call  
- **Improvement**: 98% fewer API calls

#### Scenario 3: Dashboard Data Loading
- **Without optimization**: Multiple queries, new connections
- **With optimizations**: Cached data + pooled connections
- **Improvement**: 70-90% faster loading

## Best Practices

### When to Use Caching
- ✅ Frequently accessed, relatively static data (contacts, projects)
- ✅ Data that doesn't change often (user profiles, settings)
- ❌ Real-time data (live chat, notifications)
- ❌ Highly dynamic data (current timestamps, random data)

### When to Use Batching
- ✅ Bulk imports/exports
- ✅ Data synchronization
- ✅ Cleanup operations
- ❌ Single record operations
- ❌ Operations requiring immediate feedback

### Cache Invalidation Strategy
- Invalidate on write operations (create, update, delete)
- Use table-level invalidation for related data changes
- Consider user-level invalidation for profile changes
- Monitor cache hit rates and adjust TTL accordingly

## Migration Guide

### Updating Existing Tools
To add optimizations to existing agent tools:

1. **Add caching to read operations**:
```python
@cached_query("table_name", ttl=300)
async def get_records(user_id: str, ...):
```

2. **Add cache invalidation to write operations**:
```python
async def create_record(user_id: str, ...):
    # Create record
    await get_cache().invalidate_table(user_id, "table_name")
```

3. **Use connection pooling**:
```python
result = await with_pooled_connection(query_function, user_id, jwt_token)
```

4. **Add batch operations for bulk scenarios**:
```python
@tool
async def batch_create_records(user_id: str, records_data: str, ...):
    records = json.loads(records_data)
    return await batch_insert_records("table_name", records, user_id, jwt_token)
```

### Testing Optimizations
Use the example script to test optimizations:

```bash
cd strands-multi-agent-system
python examples/optimization_usage.py
```

## Troubleshooting

### Common Issues

#### Cache Not Working
- Check if `OPTIMIZATION_CACHE_ENABLED=true`
- Verify cache TTL settings
- Check logs for cache hit/miss information

#### Connection Pool Issues  
- Monitor pool statistics via `/api/optimization/stats`
- Check connection limits and timeouts
- Review pool cleanup logs

#### Batch Operation Failures
- Verify batch size limits
- Check for data validation errors
- Review individual operation error messages

### Monitoring and Debugging
- Use `/api/optimization/stats` endpoint for real-time metrics
- Enable debug logging for detailed operation traces
- Monitor Supabase dashboard for API usage patterns
- Track performance improvements with before/after comparisons

## Future Enhancements

### Planned Improvements
- **Redis integration** - External cache for multi-instance deployments
- **Query result compression** - Reduce memory usage for large datasets
- **Adaptive TTL** - Dynamic cache expiration based on usage patterns
- **Batch operation queuing** - Automatic batching of rapid operations
- **Cache warming** - Pre-populate cache with frequently accessed data

### Metrics and Analytics
- **Cost tracking** - Monitor Supabase API usage reduction
- **Performance dashboards** - Real-time optimization metrics
- **A/B testing** - Compare optimized vs non-optimized performance
- **Alerting** - Notifications for optimization issues or degradation