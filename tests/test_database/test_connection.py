"""
Tests for database connection module.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import asyncpg
from fmcsa_system.database.connection import DatabasePool


class TestDatabasePool:
    """Test database connection pool."""
    
    @pytest.mark.asyncio
    async def test_initialize_pool_success(self):
        """Test successful pool initialization."""
        with patch("asyncpg.create_pool") as mock_create:
            mock_pool = AsyncMock()
            mock_create.return_value = mock_pool
            
            pool = DatabasePool()
            await pool.initialize()
            
            assert pool.pool == mock_pool
            mock_create.assert_called_once()
            
            # Check connection parameters
            call_args = mock_create.call_args[1]
            assert call_args["min_size"] == 5
            assert call_args["max_size"] == 20
            assert call_args["max_inactive_connection_lifetime"] == 300
    
    @pytest.mark.asyncio
    async def test_initialize_pool_failure(self):
        """Test pool initialization failure."""
        with patch("asyncpg.create_pool") as mock_create:
            mock_create.side_effect = Exception("Connection failed")
            
            pool = DatabasePool()
            with pytest.raises(Exception, match="Connection failed"):
                await pool.initialize()
    
    @pytest.mark.asyncio
    async def test_close_pool(self):
        """Test closing connection pool."""
        pool = DatabasePool()
        pool.pool = AsyncMock()
        
        await pool.close()
        
        pool.pool.close.assert_called_once()
        assert pool.pool is None
    
    @pytest.mark.asyncio
    async def test_execute_query(self):
        """Test executing a query."""
        pool = DatabasePool()
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.execute.return_value = "INSERT 0 1"
        pool.pool = mock_pool
        
        result = await pool.execute("INSERT INTO test VALUES ($1)", "value")
        
        assert result == "INSERT 0 1"
        mock_conn.execute.assert_called_once_with("INSERT INTO test VALUES ($1)", "value")
    
    @pytest.mark.asyncio
    async def test_fetch_query(self):
        """Test fetching query results."""
        pool = DatabasePool()
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        expected_data = [{"id": 1, "name": "test"}]
        mock_conn.fetch.return_value = expected_data
        pool.pool = mock_pool
        
        result = await pool.fetch("SELECT * FROM test")
        
        assert result == expected_data
        mock_conn.fetch.assert_called_once_with("SELECT * FROM test")
    
    @pytest.mark.asyncio
    async def test_fetchrow_query(self):
        """Test fetching single row."""
        pool = DatabasePool()
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        expected_data = {"id": 1, "name": "test"}
        mock_conn.fetchrow.return_value = expected_data
        pool.pool = mock_pool
        
        result = await pool.fetchrow("SELECT * FROM test WHERE id = $1", 1)
        
        assert result == expected_data
        mock_conn.fetchrow.assert_called_once_with("SELECT * FROM test WHERE id = $1", 1)
    
    @pytest.mark.asyncio
    async def test_fetchval_query(self):
        """Test fetching single value."""
        pool = DatabasePool()
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        mock_conn.fetchval.return_value = 42
        pool.pool = mock_pool
        
        result = await pool.fetchval("SELECT COUNT(*) FROM test")
        
        assert result == 42
        mock_conn.fetchval.assert_called_once_with("SELECT COUNT(*) FROM test")
    
    @pytest.mark.asyncio
    async def test_transaction(self):
        """Test transaction handling."""
        pool = DatabasePool()
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_tx = AsyncMock()
        
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.transaction.return_value.__aenter__.return_value = mock_tx
        pool.pool = mock_pool
        
        async with pool.transaction() as tx:
            assert tx is not None
        
        mock_conn.transaction.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_batch(self):
        """Test batch execution."""
        pool = DatabasePool()
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        pool.pool = mock_pool
        
        data = [(1, "test1"), (2, "test2")]
        await pool.execute_batch(
            "INSERT INTO test VALUES ($1, $2)",
            data
        )
        
        mock_conn.executemany.assert_called_once_with(
            "INSERT INTO test VALUES ($1, $2)",
            data
        )