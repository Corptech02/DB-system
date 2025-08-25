"""
Database connection management for FMCSA system using asyncpg.
Follows patterns from rag_agent with optimizations for high-volume data.
"""

import os
import json
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple, AsyncIterator
from datetime import datetime, date
from contextlib import asynccontextmanager
from uuid import UUID
from decimal import Decimal

import asyncpg
from asyncpg.pool import Pool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class DatabasePool:
    """
    Manages PostgreSQL connection pool for high-performance async operations.
    Optimized for 2.2M+ record operations with connection pooling best practices.
    """
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database pool.
        
        Args:
            database_url: PostgreSQL connection URL (defaults to DATABASE_URL env var)
        """
        self.database_url = database_url or os.getenv("DATABASE_URL")
        if not self.database_url:
            # Try to construct from individual components
            db_host = os.getenv("DB_HOST", "localhost")
            db_port = os.getenv("DB_PORT", "5432")
            db_name = os.getenv("DB_NAME", "fmcsa_db")
            db_user = os.getenv("DB_USER", "postgres")
            db_pass = os.getenv("DB_PASSWORD", "")
            
            if db_pass:
                self.database_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
            else:
                self.database_url = f"postgresql://{db_user}@{db_host}:{db_port}/{db_name}"
        
        self.pool: Optional[Pool] = None
        self._prepared_statements: Dict[str, str] = {}
    
    async def initialize(self):
        """
        Create connection pool with optimized settings for large datasets.
        """
        if self.pool:
            return
        
        try:
            # Create pool with settings optimized for FMCSA workload
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=5,                              # Minimum connections
                max_size=20,                             # Maximum connections
                max_inactive_connection_lifetime=300,    # 5 minutes idle timeout
                command_timeout=60,                      # Query timeout
                max_queries=50000,                       # Queries before connection reset
                max_cached_statement_lifetime=3600,      # Cache prepared statements for 1 hour
            )
            
            # Test the connection
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            
            logger.info(f"Database pool initialized with {self.pool._minsize}-{self.pool._maxsize} connections")
            
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    async def close(self):
        """Close connection pool gracefully."""
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("Database connection pool closed")
    
    @asynccontextmanager
    async def acquire(self):
        """
        Acquire a connection from the pool.
        
        Yields:
            asyncpg.Connection: Database connection
        """
        if not self.pool:
            await self.initialize()
        
        async with self.pool.acquire() as connection:
            yield connection
    
    async def execute(self, query: str, *args, timeout: float = None) -> str:
        """
        Execute a query without returning results.
        
        Args:
            query: SQL query to execute
            *args: Query parameters
            timeout: Query timeout in seconds
        
        Returns:
            Command status
        """
        async with self.acquire() as conn:
            return await conn.execute(query, *args, timeout=timeout)
    
    async def fetch(self, query: str, *args, timeout: float = None) -> List[asyncpg.Record]:
        """
        Fetch multiple rows.
        
        Args:
            query: SQL query
            *args: Query parameters
            timeout: Query timeout in seconds
        
        Returns:
            List of records
        """
        async with self.acquire() as conn:
            return await conn.fetch(query, *args, timeout=timeout)
    
    async def fetchrow(self, query: str, *args, timeout: float = None) -> Optional[asyncpg.Record]:
        """
        Fetch a single row.
        
        Args:
            query: SQL query
            *args: Query parameters
            timeout: Query timeout in seconds
        
        Returns:
            Single record or None
        """
        async with self.acquire() as conn:
            return await conn.fetchrow(query, *args, timeout=timeout)
    
    async def fetchval(self, query: str, *args, column: int = 0, timeout: float = None) -> Any:
        """
        Fetch a single value.
        
        Args:
            query: SQL query
            *args: Query parameters
            column: Column index to return
            timeout: Query timeout in seconds
        
        Returns:
            Single value
        """
        async with self.acquire() as conn:
            return await conn.fetchval(query, *args, column=column, timeout=timeout)
    
    async def batch_insert(
        self,
        table: str,
        records: List[Dict[str, Any]],
        on_conflict: Optional[str] = None,
        returning: Optional[str] = None
    ) -> List[asyncpg.Record]:
        """
        Perform batch insert using COPY for optimal performance.
        
        Args:
            table: Table name
            records: List of dictionaries to insert
            on_conflict: ON CONFLICT clause
            returning: RETURNING clause
        
        Returns:
            Inserted records if returning is specified
        """
        if not records:
            return []
        
        # Get column names from first record
        columns = list(records[0].keys())
        
        async with self.acquire() as conn:
            # Use COPY for best performance with large datasets
            if len(records) > 1000 and not on_conflict and not returning:
                # For large inserts without conflict handling, use COPY
                await conn.copy_records_to_table(
                    table,
                    records=[tuple(r[col] for col in columns) for r in records],
                    columns=columns
                )
                return []
            else:
                # For smaller inserts or when we need conflict handling
                values_placeholder = ','.join(
                    f"({','.join(f'${i+j*len(columns)+1}' for i in range(len(columns)))})"
                    for j in range(len(records))
                )
                
                query = f"""
                    INSERT INTO {table} ({','.join(columns)})
                    VALUES {values_placeholder}
                """
                
                if on_conflict:
                    query += f" {on_conflict}"
                
                if returning:
                    query += f" RETURNING {returning}"
                
                # Flatten values
                values = []
                for record in records:
                    values.extend(record[col] for col in columns)
                
                if returning:
                    return await conn.fetch(query, *values)
                else:
                    await conn.execute(query, *values)
                    return []
    
    async def prepare_statement(self, name: str, query: str) -> None:
        """
        Prepare a statement for repeated execution.
        
        Args:
            name: Statement name
            query: SQL query to prepare
        """
        async with self.acquire() as conn:
            stmt = await conn.prepare(query)
            self._prepared_statements[name] = query
    
    async def execute_prepared(
        self,
        name: str,
        *args,
        fetch: bool = True
    ) -> Optional[List[asyncpg.Record]]:
        """
        Execute a prepared statement.
        
        Args:
            name: Statement name
            *args: Query parameters
            fetch: Whether to fetch results
        
        Returns:
            Query results if fetch=True
        """
        if name not in self._prepared_statements:
            raise ValueError(f"Prepared statement '{name}' not found")
        
        async with self.acquire() as conn:
            stmt = await conn.prepare(self._prepared_statements[name])
            if fetch:
                return await stmt.fetch(*args)
            else:
                await stmt.execute(*args)
                return None
    
    async def stream_query(
        self,
        query: str,
        *args,
        batch_size: int = 1000
    ) -> AsyncIterator[List[asyncpg.Record]]:
        """
        Stream query results in batches for memory efficiency.
        
        Args:
            query: SQL query
            *args: Query parameters
            batch_size: Number of records per batch
        
        Yields:
            Batches of records
        """
        async with self.acquire() as conn:
            async with conn.transaction():
                cursor = await conn.cursor(query, *args)
                
                while True:
                    batch = await cursor.fetch(batch_size)
                    if not batch:
                        break
                    yield batch


# Global database pool instance
db_pool = DatabasePool()


# Convenience functions
async def initialize_database():
    """Initialize the global database connection pool."""
    await db_pool.initialize()


async def close_database():
    """Close the global database connection pool."""
    await db_pool.close()


async def test_connection() -> bool:
    """
    Test database connection and verify schema.
    
    Returns:
        True if connection successful and schema exists
    """
    try:
        # Test basic connectivity
        result = await db_pool.fetchval("SELECT 1")
        if result != 1:
            return False
        
        # Check if carriers table exists
        exists = await db_pool.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'carriers'
            )
        """)
        
        if not exists:
            logger.warning("Carriers table does not exist. Run schema migration.")
            return False
        
        logger.info("Database connection test successful")
        return True
        
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False


async def get_carrier_by_usdot(usdot_number: int) -> Optional[Dict[str, Any]]:
    """
    Get carrier by USDOT number.
    
    Args:
        usdot_number: USDOT number
    
    Returns:
        Carrier data or None
    """
    result = await db_pool.fetchrow(
        """
        SELECT 
            id::text,
            usdot_number,
            legal_name,
            dba_name,
            physical_address,
            physical_city,
            physical_state,
            physical_zip,
            telephone,
            email,
            entity_type,
            operating_status,
            liability_insurance_date,
            liability_insurance_amount,
            created_at,
            updated_at
        FROM carriers
        WHERE usdot_number = $1
        """,
        usdot_number
    )
    
    if result:
        return dict(result)
    return None


async def search_carriers(
    filters: Dict[str, Any],
    limit: int = 100,
    offset: int = 0
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Search carriers with filters and pagination.
    
    Args:
        filters: Search filters
        limit: Maximum results
        offset: Skip records
    
    Returns:
        Tuple of (results, total_count)
    """
    # Build dynamic query
    where_clauses = ["1=1"]
    params = []
    param_count = 0
    
    if filters.get("usdot_number"):
        param_count += 1
        where_clauses.append(f"usdot_number = ${param_count}")
        params.append(filters["usdot_number"])
    
    if filters.get("state"):
        param_count += 1
        where_clauses.append(f"physical_state = ${param_count}")
        params.append(filters["state"])
    
    if filters.get("entity_type"):
        param_count += 1
        where_clauses.append(f"entity_type = ${param_count}")
        params.append(filters["entity_type"])
    
    if filters.get("operating_status"):
        param_count += 1
        where_clauses.append(f"operating_status = ${param_count}")
        params.append(filters["operating_status"])
    
    if filters.get("insurance_expiring_days"):
        param_count += 1
        where_clauses.append(f"""
            liability_insurance_date BETWEEN CURRENT_DATE 
            AND CURRENT_DATE + INTERVAL '1 day' * ${param_count}
        """)
        params.append(filters["insurance_expiring_days"])
    
    where_sql = " AND ".join(where_clauses)
    
    # Get total count
    count_query = f"SELECT COUNT(*) FROM carriers WHERE {where_sql}"
    total_count = await db_pool.fetchval(count_query, *params)
    
    # Get results
    param_count += 1
    limit_param = param_count
    params.append(limit)
    
    param_count += 1
    offset_param = param_count
    params.append(offset)
    
    results_query = f"""
        SELECT 
            id::text,
            usdot_number,
            legal_name,
            dba_name,
            physical_state,
            physical_city,
            entity_type,
            operating_status,
            liability_insurance_date,
            power_units,
            drivers
        FROM carriers
        WHERE {where_sql}
        ORDER BY legal_name
        LIMIT ${limit_param} OFFSET ${offset_param}
    """
    
    results = await db_pool.fetch(results_query, *params)
    
    return [dict(r) for r in results], total_count


async def get_insurance_expiring_soon(days: int = 30) -> List[Dict[str, Any]]:
    """
    Get carriers with insurance expiring soon.
    
    Args:
        days: Days ahead to check
    
    Returns:
        List of carriers with expiring insurance
    """
    results = await db_pool.fetch(
        "SELECT * FROM get_insurance_expiring($1)",
        days
    )
    
    return [dict(r) for r in results]


async def create_partition_if_needed(date: datetime) -> None:
    """
    Create partition for given date if it doesn't exist.
    
    Args:
        date: Date to create partition for
    """
    await db_pool.execute("SELECT create_monthly_partition()")


async def refresh_statistics() -> None:
    """Refresh materialized view for carrier statistics."""
    await db_pool.execute("SELECT refresh_carrier_statistics()")