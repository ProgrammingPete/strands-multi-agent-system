"""
Supabase batch operations for reducing API calls.

This module provides utilities for batching multiple operations
into single API calls, reducing network overhead and improving performance.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import json

from utils.supabase_client import get_supabase_client, SupabaseQueryError

logger = logging.getLogger(__name__)


class BatchOperationType(Enum):
    """Types of batch operations."""
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    UPSERT = "upsert"


@dataclass
class BatchOperation:
    """Represents a single operation in a batch."""
    operation_type: BatchOperationType
    table: str
    data: Dict[str, Any]
    filters: Optional[Dict[str, Any]] = None  # For updates/deletes
    id_field: str = "id"  # Field to use for matching in updates


@dataclass
class BatchResult:
    """Result of a batch operation."""
    success: bool
    operation_count: int
    results: List[Dict[str, Any]]
    errors: List[str]
    execution_time_ms: int


class SupabaseBatcher:
    """
    Utility for batching Supabase operations to reduce API calls.
    
    Features:
    - Batch inserts, updates, deletes, and upserts
    - Automatic batching by table and operation type
    - Error handling and partial success reporting
    - User-scoped operations with RLS support
    """
    
    def __init__(self, max_batch_size: int = 100):
        """
        Initialize the batcher.
        
        Args:
            max_batch_size: Maximum number of operations per batch
        """
        self.max_batch_size = max_batch_size
        self.supabase_wrapper = get_supabase_client()
        logger.info(f"SupabaseBatcher initialized with max_batch_size={max_batch_size}")
    
    async def execute_batch(
        self,
        operations: List[BatchOperation],
        user_id: str,
        jwt_token: Optional[str] = None
    ) -> BatchResult:
        """
        Execute a batch of operations.
        
        Args:
            operations: List of operations to execute
            user_id: User ID for scoping
            jwt_token: Optional JWT token for user-scoped operations
            
        Returns:
            BatchResult with execution details
        """
        import time
        start_time = time.time()
        
        try:
            logger.info(f"Executing batch of {len(operations)} operations for user {user_id}")
            
            # Group operations by table and type for efficient batching
            grouped_ops = self._group_operations(operations)
            
            all_results = []
            all_errors = []
            
            # Execute each group
            for (table, op_type), ops in grouped_ops.items():
                try:
                    results = await self._execute_operation_group(
                        table, op_type, ops, user_id, jwt_token
                    )
                    all_results.extend(results)
                except Exception as e:
                    error_msg = f"Failed to execute {op_type.value} operations on {table}: {str(e)}"
                    all_errors.append(error_msg)
                    logger.error(error_msg)
            
            execution_time = int((time.time() - start_time) * 1000)
            
            return BatchResult(
                success=len(all_errors) == 0,
                operation_count=len(operations),
                results=all_results,
                errors=all_errors,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            logger.error(f"Batch execution failed: {e}", exc_info=True)
            
            return BatchResult(
                success=False,
                operation_count=len(operations),
                results=[],
                errors=[str(e)],
                execution_time_ms=execution_time
            )
    
    def _group_operations(
        self,
        operations: List[BatchOperation]
    ) -> Dict[Tuple[str, BatchOperationType], List[BatchOperation]]:
        """
        Group operations by table and operation type for efficient batching.
        
        Args:
            operations: List of operations to group
            
        Returns:
            Dictionary mapping (table, operation_type) to list of operations
        """
        grouped = {}
        
        for op in operations:
            key = (op.table, op.operation_type)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(op)
        
        return grouped
    
    async def _execute_operation_group(
        self,
        table: str,
        operation_type: BatchOperationType,
        operations: List[BatchOperation],
        user_id: str,
        jwt_token: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a group of operations of the same type on the same table.
        
        Args:
            table: Table name
            operation_type: Type of operation
            operations: List of operations
            user_id: User ID for scoping
            jwt_token: Optional JWT token for user-scoped operations
            
        Returns:
            List of results from the operations
        """
        # Get appropriate client
        if jwt_token:
            client = self.supabase_wrapper.create_user_scoped_client(jwt_token)
            table_ref = client.schema("api").table(table)
        else:
            client = self.supabase_wrapper.client
            table_ref = client.schema("api").table(table)
        
        # Split into batches if needed
        batches = [
            operations[i:i + self.max_batch_size]
            for i in range(0, len(operations), self.max_batch_size)
        ]
        
        all_results = []
        
        for batch in batches:
            if operation_type == BatchOperationType.INSERT:
                results = await self._execute_batch_insert(table_ref, batch, user_id)
            elif operation_type == BatchOperationType.UPDATE:
                results = await self._execute_batch_update(table_ref, batch, user_id)
            elif operation_type == BatchOperationType.DELETE:
                results = await self._execute_batch_delete(table_ref, batch, user_id)
            elif operation_type == BatchOperationType.UPSERT:
                results = await self._execute_batch_upsert(table_ref, batch, user_id)
            else:
                raise ValueError(f"Unsupported operation type: {operation_type}")
            
            all_results.extend(results)
        
        return all_results
    
    async def _execute_batch_insert(
        self,
        table_ref,
        operations: List[BatchOperation],
        user_id: str
    ) -> List[Dict[str, Any]]:
        """Execute batch insert operations."""
        # Prepare data for batch insert
        insert_data = []
        for op in operations:
            data = op.data.copy()
            data['user_id'] = user_id  # Ensure user_id is set for RLS
            insert_data.append(data)
        
        # Execute batch insert
        response = table_ref.insert(insert_data).execute()
        
        logger.info(f"Batch inserted {len(insert_data)} records")
        return response.data
    
    async def _execute_batch_update(
        self,
        table_ref,
        operations: List[BatchOperation],
        user_id: str
    ) -> List[Dict[str, Any]]:
        """Execute batch update operations."""
        # Note: Supabase doesn't support true batch updates with different data
        # We'll execute individual updates but log them as a batch
        results = []
        
        for op in operations:
            if not op.filters:
                raise ValueError("Update operations require filters")
            
            # Build update query
            query = table_ref.update(op.data)
            
            # Apply filters
            for field, value in op.filters.items():
                query = query.eq(field, value)
            
            # Ensure user scoping for RLS
            query = query.eq('user_id', user_id)
            
            response = query.execute()
            results.extend(response.data)
        
        logger.info(f"Batch updated {len(operations)} records")
        return results
    
    async def _execute_batch_delete(
        self,
        table_ref,
        operations: List[BatchOperation],
        user_id: str
    ) -> List[Dict[str, Any]]:
        """Execute batch delete operations."""
        # Collect IDs for batch delete
        ids_to_delete = []
        
        for op in operations:
            if op.filters and op.id_field in op.filters:
                ids_to_delete.append(op.filters[op.id_field])
            elif op.id_field in op.data:
                ids_to_delete.append(op.data[op.id_field])
            else:
                raise ValueError(f"Delete operation missing {op.id_field}")
        
        # Execute batch delete using IN clause
        response = (
            table_ref.delete()
            .eq('user_id', user_id)  # Ensure user scoping for RLS
            .in_(op.id_field, ids_to_delete)
            .execute()
        )
        
        logger.info(f"Batch deleted {len(ids_to_delete)} records")
        return response.data
    
    async def _execute_batch_upsert(
        self,
        table_ref,
        operations: List[BatchOperation],
        user_id: str
    ) -> List[Dict[str, Any]]:
        """Execute batch upsert operations."""
        # Prepare data for batch upsert
        upsert_data = []
        for op in operations:
            data = op.data.copy()
            data['user_id'] = user_id  # Ensure user_id is set for RLS
            upsert_data.append(data)
        
        # Execute batch upsert
        response = table_ref.upsert(upsert_data).execute()
        
        logger.info(f"Batch upserted {len(upsert_data)} records")
        return response.data


# Global batcher instance
_batcher_instance: Optional[SupabaseBatcher] = None


def get_batcher() -> SupabaseBatcher:
    """Get the global batcher instance."""
    global _batcher_instance
    if _batcher_instance is None:
        _batcher_instance = SupabaseBatcher()
    return _batcher_instance


# Convenience functions for common batch operations

async def batch_insert_records(
    table: str,
    records: List[Dict[str, Any]],
    user_id: str,
    jwt_token: Optional[str] = None
) -> BatchResult:
    """
    Batch insert multiple records into a table.
    
    Args:
        table: Table name
        records: List of records to insert
        user_id: User ID for scoping
        jwt_token: Optional JWT token for user-scoped operations
        
    Returns:
        BatchResult with execution details
    """
    operations = [
        BatchOperation(
            operation_type=BatchOperationType.INSERT,
            table=table,
            data=record
        )
        for record in records
    ]
    
    batcher = get_batcher()
    return await batcher.execute_batch(operations, user_id, jwt_token)


async def batch_update_records(
    table: str,
    updates: List[Tuple[Dict[str, Any], Dict[str, Any]]],  # (data, filters)
    user_id: str,
    jwt_token: Optional[str] = None
) -> BatchResult:
    """
    Batch update multiple records in a table.
    
    Args:
        table: Table name
        updates: List of (update_data, filter_conditions) tuples
        user_id: User ID for scoping
        jwt_token: Optional JWT token for user-scoped operations
        
    Returns:
        BatchResult with execution details
    """
    operations = [
        BatchOperation(
            operation_type=BatchOperationType.UPDATE,
            table=table,
            data=data,
            filters=filters
        )
        for data, filters in updates
    ]
    
    batcher = get_batcher()
    return await batcher.execute_batch(operations, user_id, jwt_token)


async def batch_delete_records(
    table: str,
    record_ids: List[str],
    user_id: str,
    jwt_token: Optional[str] = None,
    id_field: str = "id"
) -> BatchResult:
    """
    Batch delete multiple records from a table.
    
    Args:
        table: Table name
        record_ids: List of record IDs to delete
        user_id: User ID for scoping
        jwt_token: Optional JWT token for user-scoped operations
        id_field: Field name for the ID column
        
    Returns:
        BatchResult with execution details
    """
    operations = [
        BatchOperation(
            operation_type=BatchOperationType.DELETE,
            table=table,
            data={},
            filters={id_field: record_id},
            id_field=id_field
        )
        for record_id in record_ids
    ]
    
    batcher = get_batcher()
    return await batcher.execute_batch(operations, user_id, jwt_token)