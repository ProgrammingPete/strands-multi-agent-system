"""
Configuration for Supabase optimization features.

This module provides configuration settings for caching, batching,
and connection pooling optimizations.
"""

import os
from typing import Dict, Any
from pydantic_settings import BaseSettings


class OptimizationSettings(BaseSettings):
    """Settings for Supabase optimization features."""
    
    # Cache Configuration
    cache_enabled: bool = True
    cache_max_size: int = 1000
    cache_default_ttl: int = 300  # 5 minutes
    cache_cleanup_interval: int = 300  # 5 minutes
    
    # Connection Pool Configuration
    pool_enabled: bool = True
    pool_max_connections: int = 50
    pool_max_idle_time: int = 300  # 5 minutes
    pool_cleanup_interval: int = 60  # 1 minute
    
    # Batch Operation Configuration
    batch_enabled: bool = True
    batch_max_size: int = 100
    batch_timeout_ms: int = 5000  # 5 seconds
    
    # Cache TTL settings for different data types
    cache_ttl_contacts: int = 300      # 5 minutes
    cache_ttl_invoices: int = 180      # 3 minutes
    cache_ttl_projects: int = 600      # 10 minutes
    cache_ttl_appointments: int = 120  # 2 minutes
    cache_ttl_reviews: int = 900       # 15 minutes
    cache_ttl_campaigns: int = 1800    # 30 minutes
    
    # Performance monitoring
    monitoring_enabled: bool = True
    stats_retention_hours: int = 24
    
    class Config:
        env_prefix = "OPTIMIZATION_"
        case_sensitive = False


# Global settings instance
optimization_settings = OptimizationSettings()


def get_cache_ttl(table_name: str) -> int:
    """
    Get appropriate cache TTL for a specific table.
    
    Args:
        table_name: Name of the database table
        
    Returns:
        TTL in seconds for the table
    """
    ttl_mapping = {
        "contacts": optimization_settings.cache_ttl_contacts,
        "invoices": optimization_settings.cache_ttl_invoices,
        "projects": optimization_settings.cache_ttl_projects,
        "appointments": optimization_settings.cache_ttl_appointments,
        "reviews": optimization_settings.cache_ttl_reviews,
        "campaigns": optimization_settings.cache_ttl_campaigns,
    }
    
    return ttl_mapping.get(table_name, optimization_settings.cache_default_ttl)


def get_optimization_config() -> Dict[str, Any]:
    """
    Get current optimization configuration.
    
    Returns:
        Dictionary with all optimization settings
    """
    return {
        "cache": {
            "enabled": optimization_settings.cache_enabled,
            "max_size": optimization_settings.cache_max_size,
            "default_ttl": optimization_settings.cache_default_ttl,
            "cleanup_interval": optimization_settings.cache_cleanup_interval,
            "table_ttls": {
                "contacts": optimization_settings.cache_ttl_contacts,
                "invoices": optimization_settings.cache_ttl_invoices,
                "projects": optimization_settings.cache_ttl_projects,
                "appointments": optimization_settings.cache_ttl_appointments,
                "reviews": optimization_settings.cache_ttl_reviews,
                "campaigns": optimization_settings.cache_ttl_campaigns,
            }
        },
        "connection_pool": {
            "enabled": optimization_settings.pool_enabled,
            "max_connections": optimization_settings.pool_max_connections,
            "max_idle_time": optimization_settings.pool_max_idle_time,
            "cleanup_interval": optimization_settings.pool_cleanup_interval,
        },
        "batch_operations": {
            "enabled": optimization_settings.batch_enabled,
            "max_size": optimization_settings.batch_max_size,
            "timeout_ms": optimization_settings.batch_timeout_ms,
        },
        "monitoring": {
            "enabled": optimization_settings.monitoring_enabled,
            "stats_retention_hours": optimization_settings.stats_retention_hours,
        }
    }


def is_optimization_enabled(feature: str) -> bool:
    """
    Check if a specific optimization feature is enabled.
    
    Args:
        feature: Feature name ('cache', 'pool', 'batch', 'monitoring')
        
    Returns:
        True if feature is enabled, False otherwise
    """
    feature_mapping = {
        "cache": optimization_settings.cache_enabled,
        "pool": optimization_settings.pool_enabled,
        "batch": optimization_settings.batch_enabled,
        "monitoring": optimization_settings.monitoring_enabled,
    }
    
    return feature_mapping.get(feature, False)