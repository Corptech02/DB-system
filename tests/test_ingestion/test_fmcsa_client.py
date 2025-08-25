"""
Tests for FMCSA API client.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import aiohttp
from datetime import datetime
from fmcsa_system.ingestion.fmcsa_client import FMCSAClient


class TestFMCSAClient:
    """Test FMCSA API client."""
    
    @pytest.mark.asyncio
    async def test_fetch_carriers_success(self, sample_raw_fmcsa_data):
        """Test successful carrier fetching."""
        client = FMCSAClient()
        
        with patch("aiohttp.ClientSession") as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=[sample_raw_fmcsa_data])
            
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            results = await client.fetch_carriers(limit=1, offset=0)
            
            assert len(results) == 1
            assert results[0]["dot_number"] == "123456"
    
    @pytest.mark.asyncio
    async def test_fetch_carriers_with_filters(self):
        """Test fetching carriers with filters."""
        client = FMCSAClient()
        
        with patch("aiohttp.ClientSession") as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=[])
            
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            await client.fetch_carriers(
                limit=100,
                offset=0,
                state="TX",
                entity_type="CARRIER"
            )
            
            # Check that filters were added to URL
            call_args = mock_session.return_value.__aenter__.return_value.get.call_args
            url = call_args[0][0]
            assert "phy_state=TX" in url
            assert "entity_type=CARRIER" in url
    
    @pytest.mark.asyncio
    async def test_fetch_carriers_retry_on_error(self):
        """Test retry logic on API error."""
        client = FMCSAClient()
        client.max_retries = 2
        
        with patch("aiohttp.ClientSession") as mock_session:
            # First call fails, second succeeds
            mock_response_fail = AsyncMock()
            mock_response_fail.status = 500
            
            mock_response_success = AsyncMock()
            mock_response_success.status = 200
            mock_response_success.json = AsyncMock(return_value=[])
            
            mock_get = AsyncMock()
            mock_get.__aenter__.side_effect = [
                mock_response_fail,
                mock_response_success
            ]
            
            mock_session.return_value.__aenter__.return_value.get.return_value = mock_get
            
            with patch("asyncio.sleep"):  # Skip delay in tests
                results = await client.fetch_carriers(limit=100, offset=0)
            
            assert results == []
            assert mock_get.__aenter__.call_count == 2
    
    @pytest.mark.asyncio
    async def test_fetch_carriers_max_retries_exceeded(self):
        """Test max retries exceeded."""
        client = FMCSAClient()
        client.max_retries = 2
        
        with patch("aiohttp.ClientSession") as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 500
            
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            with patch("asyncio.sleep"):  # Skip delay in tests
                with pytest.raises(Exception, match="Failed to fetch"):
                    await client.fetch_carriers(limit=100, offset=0)
    
    @pytest.mark.asyncio
    async def test_get_total_count(self):
        """Test getting total carrier count."""
        client = FMCSAClient()
        
        with patch("aiohttp.ClientSession") as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=[{"count": "2500000"}])
            
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            count = await client.get_total_count()
            
            assert count == 2500000
    
    @pytest.mark.asyncio
    async def test_get_modified_carriers(self):
        """Test fetching modified carriers."""
        client = FMCSAClient()
        since_date = datetime(2024, 1, 1)
        
        with patch("aiohttp.ClientSession") as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=[])
            
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            await client.get_modified_carriers(since_date, limit=100)
            
            # Check that date filter was added
            call_args = mock_session.return_value.__aenter__.return_value.get.call_args
            url = call_args[0][0]
            assert "$where=" in url
            assert "mcs150_date" in url
    
    def test_build_url_with_filters(self):
        """Test URL building with various filters."""
        client = FMCSAClient()
        
        url = client._build_url(
            limit=100,
            offset=50,
            state="CA",
            entity_type="BROKER",
            operating_status="ACTIVE"
        )
        
        assert "$limit=100" in url
        assert "$offset=50" in url
        assert "phy_state=CA" in url
        assert "entity_type=BROKER" in url
        assert "operating_status=ACTIVE" in url
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test rate limiting between requests."""
        client = FMCSAClient()
        client.rate_limit_delay = 0.1  # 100ms delay
        
        with patch("aiohttp.ClientSession") as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=[])
            
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            start_time = datetime.now()
            
            # Make two requests
            await client.fetch_carriers(limit=10, offset=0)
            await client.fetch_carriers(limit=10, offset=10)
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            # Should have at least one rate limit delay
            assert elapsed >= 0.1