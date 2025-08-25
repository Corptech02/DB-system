"""
Pytest configuration and fixtures for FMCSA system tests.
"""

import pytest
import asyncio
import asyncpg
from typing import AsyncGenerator
from unittest.mock import Mock, AsyncMock
import os
from datetime import datetime, date

# Set test environment
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "postgresql://test_user:test_pass@localhost:5432/test_fmcsa"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_db_pool():
    """Mock database pool for testing."""
    pool = AsyncMock(spec=asyncpg.Pool)
    
    # Mock connection
    conn = AsyncMock()
    conn.fetch = AsyncMock(return_value=[])
    conn.fetchrow = AsyncMock(return_value=None)
    conn.fetchval = AsyncMock(return_value=0)
    conn.execute = AsyncMock(return_value="INSERT 0 1")
    
    pool.acquire = AsyncMock(return_value=conn)
    pool.__aenter__ = AsyncMock(return_value=conn)
    pool.__aexit__ = AsyncMock(return_value=None)
    
    return pool


@pytest.fixture
def sample_carrier_data():
    """Sample carrier data for testing."""
    return {
        "usdot_number": 123456,
        "legal_name": "Test Carrier LLC",
        "dba_name": "Test Express",
        "physical_address": "123 Main St",
        "physical_city": "Houston",
        "physical_state": "TX",
        "physical_zip": "77001",
        "mailing_address": "PO Box 456",
        "mailing_city": "Houston",
        "mailing_state": "TX",
        "mailing_zip": "77002",
        "telephone": "713-555-0100",
        "email": "info@testcarrier.com",
        "entity_type": "CARRIER",
        "operating_status": "ACTIVE",
        "power_units": 25,
        "drivers": 30,
        "hazmat_flag": True,
        "liability_insurance_date": date(2024, 6, 30),
        "liability_insurance_amount": 1000000.00,
        "safety_rating": "SATISFACTORY",
        "mcs_150_date": date(2024, 1, 15),
        "cargo_carried": "General Freight",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }


@pytest.fixture
def sample_raw_fmcsa_data():
    """Sample raw FMCSA API response data."""
    return {
        "dot_number": "123456",
        "legal_name": "TEST CARRIER LLC",
        "dba_name": "TEST EXPRESS",
        "phy_street": "123 MAIN ST",
        "phy_city": "HOUSTON",
        "phy_state": "TX",
        "phy_zip": "77001",
        "phy_country": "US",
        "mailing_street": "PO BOX 456",
        "mailing_city": "HOUSTON",
        "mailing_state": "TX",
        "mailing_zip": "77002",
        "mailing_country": "US",
        "telephone": "7135550100",
        "email_address": "info@testcarrier.com",
        "entity_type": "CARRIER",
        "operating_status": "ACTIVE",
        "nbr_power_unit": "25",
        "driver_total": "30",
        "carrier_operation": "Interstate",
        "hm_flag": "Y",
        "pc_flag": "N",
        "mcs150_date": "01/15/2024",
        "mcs150_mileage": "500000",
        "mcs150_mileage_year": "2023",
        "add_date": "01/01/2020",
        "oic_state": "TX",
        "cargo_carried": "General Freight",
        "rating_date": "06/01/2023",
        "review_date": "06/01/2023",
        "company_rating": "SATISFACTORY"
    }


@pytest.fixture
def mock_fmcsa_client():
    """Mock FMCSA client for testing."""
    client = AsyncMock()
    client.fetch_carriers = AsyncMock(return_value=[])
    client.get_total_count = AsyncMock(return_value=100)
    return client


@pytest.fixture
async def test_app():
    """Create test FastAPI application."""
    from fmcsa_system.api.main import app
    return app


@pytest.fixture
def search_filters():
    """Sample search filters for testing."""
    return {
        "state": "TX",
        "operating_status": "ACTIVE",
        "min_power_units": 10,
        "insurance_expiring_days": 30
    }