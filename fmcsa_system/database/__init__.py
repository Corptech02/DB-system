"""
Database module for FMCSA system.
Provides connection pooling and database operations.
"""

from .connection import (
    DatabasePool,
    db_pool,
    initialize_database,
    close_database,
    test_connection,
    get_carrier_by_usdot,
    search_carriers,
    get_insurance_expiring_soon,
    create_partition_if_needed,
    refresh_statistics
)

__all__ = [
    'DatabasePool',
    'db_pool',
    'initialize_database',
    'close_database',
    'test_connection',
    'get_carrier_by_usdot',
    'search_carriers',
    'get_insurance_expiring_soon',
    'create_partition_if_needed',
    'refresh_statistics'
]