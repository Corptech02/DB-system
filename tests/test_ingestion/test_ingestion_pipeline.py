"""
Tests for ingestion pipeline.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock, call
from datetime import datetime, date
from fmcsa_system.ingestion.ingestion_pipeline import (
    IngestionPipeline,
    CarrierDataNormalizer,
    IngestionStats
)


class TestCarrierDataNormalizer:
    """Test carrier data normalization."""
    
    def test_normalize_basic_fields(self, sample_raw_fmcsa_data):
        """Test normalization of basic fields."""
        normalizer = CarrierDataNormalizer()
        result = normalizer.normalize(sample_raw_fmcsa_data)
        
        assert result["usdot_number"] == 123456
        assert result["legal_name"] == "TEST CARRIER LLC"
        assert result["dba_name"] == "TEST EXPRESS"
        assert result["physical_address"] == "123 MAIN ST"
        assert result["physical_city"] == "HOUSTON"
        assert result["physical_state"] == "TX"
        assert result["physical_zip"] == "77001"
    
    def test_normalize_numeric_fields(self, sample_raw_fmcsa_data):
        """Test normalization of numeric fields."""
        normalizer = CarrierDataNormalizer()
        result = normalizer.normalize(sample_raw_fmcsa_data)
        
        assert result["power_units"] == 25
        assert result["drivers"] == 30
    
    def test_normalize_boolean_fields(self, sample_raw_fmcsa_data):
        """Test normalization of boolean fields."""
        normalizer = CarrierDataNormalizer()
        result = normalizer.normalize(sample_raw_fmcsa_data)
        
        assert result["hazmat_flag"] is True  # "Y" -> True
    
    def test_normalize_date_fields(self):
        """Test date field normalization."""
        normalizer = CarrierDataNormalizer()
        
        data = {"mcs150_date": "06/15/2024"}
        result = normalizer.normalize(data)
        
        assert result["mcs_150_date"] == date(2024, 6, 15)
    
    def test_normalize_missing_fields(self):
        """Test handling of missing fields."""
        normalizer = CarrierDataNormalizer()
        result = normalizer.normalize({})
        
        assert result["usdot_number"] is None
        assert result["legal_name"] is None
        assert result["power_units"] is None
        assert result["hazmat_flag"] is False
    
    def test_normalize_invalid_date(self):
        """Test handling of invalid date."""
        normalizer = CarrierDataNormalizer()
        
        data = {"mcs150_date": "invalid"}
        result = normalizer.normalize(data)
        
        assert result["mcs_150_date"] is None
    
    def test_clean_phone_number(self):
        """Test phone number cleaning."""
        normalizer = CarrierDataNormalizer()
        
        assert normalizer._clean_phone("7135551234") == "713-555-1234"
        assert normalizer._clean_phone("713-555-1234") == "713-555-1234"
        assert normalizer._clean_phone("17135551234") == "713-555-1234"
        assert normalizer._clean_phone("invalid") == "invalid"


class TestIngestionPipeline:
    """Test ingestion pipeline."""
    
    @pytest.mark.asyncio
    async def test_run_full_ingestion(self, mock_fmcsa_client, mock_db_pool):
        """Test full ingestion process."""
        pipeline = IngestionPipeline(
            fmcsa_client=mock_fmcsa_client,
            batch_size=100
        )
        
        # Mock data
        mock_fmcsa_client.get_total_count.return_value = 200
        mock_fmcsa_client.fetch_carriers.side_effect = [
            [{"dot_number": str(i)} for i in range(100)],  # First batch
            [{"dot_number": str(i)} for i in range(100, 200)]  # Second batch
        ]
        
        with patch("fmcsa_system.database.db_pool", mock_db_pool):
            stats = await pipeline.run_full_ingestion()
        
        assert stats.total_fetched == 200
        assert mock_fmcsa_client.fetch_carriers.call_count == 2
    
    @pytest.mark.asyncio
    async def test_run_incremental_update(self, mock_fmcsa_client, mock_db_pool):
        """Test incremental update process."""
        pipeline = IngestionPipeline(
            fmcsa_client=mock_fmcsa_client,
            batch_size=100
        )
        
        since_date = datetime(2024, 1, 1)
        mock_fmcsa_client.get_modified_carriers.return_value = [
            {"dot_number": "123"},
            {"dot_number": "456"}
        ]
        
        with patch("fmcsa_system.database.db_pool", mock_db_pool):
            stats = await pipeline.run_incremental_update(since_date)
        
        assert stats.total_fetched == 2
        mock_fmcsa_client.get_modified_carriers.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_batch(self, mock_db_pool, sample_raw_fmcsa_data):
        """Test batch processing."""
        pipeline = IngestionPipeline(
            fmcsa_client=AsyncMock(),
            batch_size=100
        )
        
        raw_data = [sample_raw_fmcsa_data]
        
        # Mock database responses
        mock_db_pool.fetch.return_value = []  # No existing records
        
        with patch("fmcsa_system.database.db_pool", mock_db_pool):
            stats = await pipeline._process_batch(raw_data)
        
        assert stats["inserted"] == 1
        assert stats["updated"] == 0
        assert stats["errors"] == 0
    
    @pytest.mark.asyncio
    async def test_process_batch_with_update(self, mock_db_pool, sample_raw_fmcsa_data):
        """Test batch processing with updates."""
        pipeline = IngestionPipeline(
            fmcsa_client=AsyncMock(),
            batch_size=100
        )
        
        raw_data = [sample_raw_fmcsa_data]
        
        # Mock existing record
        mock_db_pool.fetch.return_value = [{"usdot_number": 123456}]
        
        with patch("fmcsa_system.database.db_pool", mock_db_pool):
            stats = await pipeline._process_batch(raw_data)
        
        assert stats["inserted"] == 0
        assert stats["updated"] == 1
        assert stats["errors"] == 0
    
    @pytest.mark.asyncio
    async def test_process_batch_with_error(self, mock_db_pool):
        """Test batch processing with normalization error."""
        pipeline = IngestionPipeline(
            fmcsa_client=AsyncMock(),
            batch_size=100
        )
        
        # Invalid data that will cause error
        raw_data = [{"invalid": "data"}]
        
        with patch("fmcsa_system.database.db_pool", mock_db_pool):
            with patch.object(pipeline.normalizer, "normalize", side_effect=Exception("Normalization error")):
                stats = await pipeline._process_batch(raw_data)
        
        assert stats["inserted"] == 0
        assert stats["updated"] == 0
        assert stats["errors"] == 1
    
    @pytest.mark.asyncio
    async def test_progress_callback(self, mock_fmcsa_client, mock_db_pool):
        """Test progress callback functionality."""
        pipeline = IngestionPipeline(
            fmcsa_client=mock_fmcsa_client,
            batch_size=100
        )
        
        progress_calls = []
        def progress_callback(current, total):
            progress_calls.append((current, total))
        
        mock_fmcsa_client.get_total_count.return_value = 100
        mock_fmcsa_client.fetch_carriers.return_value = [
            {"dot_number": str(i)} for i in range(100)
        ]
        
        with patch("fmcsa_system.database.db_pool", mock_db_pool):
            await pipeline.run_full_ingestion(progress_callback=progress_callback)
        
        assert len(progress_calls) > 0
        assert progress_calls[-1][0] == 100  # Final progress


class TestIngestionStats:
    """Test ingestion statistics."""
    
    def test_stats_initialization(self):
        """Test stats initialization."""
        stats = IngestionStats()
        
        assert stats.total_fetched == 0
        assert stats.total_inserted == 0
        assert stats.total_updated == 0
        assert stats.total_errors == 0
        assert stats.start_time is not None
        assert stats.end_time is None
        assert stats.duration_seconds == 0
    
    def test_stats_to_dict(self):
        """Test converting stats to dictionary."""
        stats = IngestionStats()
        stats.total_fetched = 100
        stats.total_inserted = 80
        stats.total_updated = 20
        
        result = stats.to_dict()
        
        assert result["total_fetched"] == 100
        assert result["total_inserted"] == 80
        assert result["total_updated"] == 20
        assert "start_time" in result
        assert "duration_seconds" in result