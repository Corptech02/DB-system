"""
Data ingestion pipeline for FMCSA carriers.
Handles batch processing, data normalization, and database updates.
"""

import os
import asyncio
import logging
import json
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, date
from decimal import Decimal
from dataclasses import dataclass
import re

from dotenv import load_dotenv

from .fmcsa_client import FMCSAClient
from ..database import db_pool, create_partition_if_needed, refresh_statistics
from ..api.models import CarrierCreate

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class IngestionStats:
    """Statistics for ingestion run."""
    start_time: datetime
    end_time: Optional[datetime] = None
    total_fetched: int = 0
    total_inserted: int = 0
    total_updated: int = 0
    total_errors: int = 0
    error_records: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.error_records is None:
            self.error_records = []
    
    @property
    def duration_seconds(self) -> float:
        """Calculate duration in seconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        total = self.total_fetched
        if total == 0:
            return 0
        return ((total - self.total_errors) / total) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "total_fetched": self.total_fetched,
            "total_inserted": self.total_inserted,
            "total_updated": self.total_updated,
            "total_errors": self.total_errors,
            "success_rate": self.success_rate,
            "error_count_by_type": self._group_errors()
        }
    
    def _group_errors(self) -> Dict[str, int]:
        """Group errors by type."""
        error_types = {}
        for error in self.error_records:
            error_type = error.get("error_type", "unknown")
            error_types[error_type] = error_types.get(error_type, 0) + 1
        return error_types


class CarrierDataNormalizer:
    """Normalizes FMCSA data to match our database schema."""
    
    # Field mapping from FMCSA to our schema
    FIELD_MAPPING = {
        'usdot_number': 'usdot_number',
        'legal_name': 'legal_name',
        'dba_name': 'dba_name',
        'phy_street': 'physical_address',
        'phy_city': 'physical_city',
        'phy_state': 'physical_state',
        'phy_zip': 'physical_zip',
        'phy_country': 'physical_country',
        'mailing_street': 'mailing_address',
        'mailing_city': 'mailing_city',
        'mailing_state': 'mailing_state',
        'mailing_zip': 'mailing_zip',
        'telephone': 'telephone',
        'fax': 'fax',
        'email_address': 'email',
        'mcs_150_date': 'mcs_150_date',
        'mcs_150_mileage_year': 'mcs_150_mileage',
        'entity_type': 'entity_type',
        'operating_status': 'operating_status',
        'out_of_service_date': 'out_of_service_date',
        'power_units': 'power_units',
        'drivers': 'drivers',
        'carrier_operation': 'carrier_operation',
        'hazmat_flag': 'hazmat_flag',
        'pc_flag': 'hazmat_placardable',
        'safety_rating': 'safety_rating',
        'safety_rating_date': 'safety_rating_date',
        'safety_review_date': 'safety_review_date',
        'liability_required_amount': 'liability_insurance_amount',
        'liability_insurance_on_file_date': 'liability_insurance_date',
        'cargo_required_amount': 'cargo_insurance_amount',
        'cargo_insurance_on_file_date': 'cargo_insurance_date',
        'bond_insurance_required_amount': 'bond_insurance_amount',
        'bond_insurance_on_file_date': 'bond_insurance_date'
    }
    
    @classmethod
    def normalize(cls, fmcsa_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize FMCSA record to our database schema.
        
        Args:
            fmcsa_record: Raw FMCSA API record
        
        Returns:
            Normalized carrier data
        """
        normalized = {}
        
        # Map fields
        for fmcsa_field, db_field in cls.FIELD_MAPPING.items():
            if fmcsa_field in fmcsa_record:
                value = fmcsa_record[fmcsa_field]
                
                # Clean and validate value
                if value is not None and value != '':
                    normalized[db_field] = cls._clean_value(db_field, value)
        
        # Parse cargo carried (comes as separate fields)
        cargo_carried = cls._extract_cargo_carried(fmcsa_record)
        if cargo_carried:
            normalized['cargo_carried'] = cargo_carried
        
        # Ensure required fields
        if 'usdot_number' not in normalized:
            raise ValueError("Missing required field: usdot_number")
        
        if 'legal_name' not in normalized or not normalized['legal_name']:
            normalized['legal_name'] = f"Unknown Carrier #{normalized.get('usdot_number', 'N/A')}"
        
        # Add raw data for reference
        normalized['raw_data'] = json.dumps(fmcsa_record)
        
        return normalized
    
    @classmethod
    def _clean_value(cls, field_name: str, value: Any) -> Any:
        """
        Clean and validate field value.
        
        Args:
            field_name: Database field name
            value: Raw value
        
        Returns:
            Cleaned value
        """
        if value is None:
            return None
        
        # Convert to string and strip whitespace
        if isinstance(value, str):
            value = value.strip()
            if value == '' or value.upper() in ['NULL', 'NONE', 'N/A']:
                return None
        
        # Handle specific field types
        if field_name in ['usdot_number', 'power_units', 'drivers', 'mcs_150_mileage']:
            # Integer fields
            try:
                return int(value) if value else None
            except (ValueError, TypeError):
                return None
        
        elif field_name in ['liability_insurance_amount', 'cargo_insurance_amount', 'bond_insurance_amount']:
            # Decimal fields
            try:
                # Remove currency symbols and commas
                if isinstance(value, str):
                    value = re.sub(r'[$,]', '', value)
                return Decimal(value) if value else None
            except (ValueError, TypeError):
                return None
        
        elif field_name.endswith('_date'):
            # Date fields
            return cls._parse_date(value)
        
        elif field_name in ['hazmat_flag', 'hazmat_placardable']:
            # Boolean fields
            if isinstance(value, str):
                return value.upper() in ['Y', 'YES', 'TRUE', '1']
            return bool(value)
        
        elif field_name in ['physical_state', 'mailing_state']:
            # State codes - uppercase and validate
            if isinstance(value, str):
                state = value.upper()[:2]
                if re.match(r'^[A-Z]{2}$', state):
                    return state
            return None
        
        elif field_name in ['physical_zip', 'mailing_zip']:
            # ZIP codes - validate format
            if isinstance(value, str):
                zip_code = re.sub(r'[^\d-]', '', value)
                if re.match(r'^\d{5}(-\d{4})?$', zip_code):
                    return zip_code
            return None
        
        elif field_name == 'telephone' or field_name == 'fax':
            # Phone numbers - basic cleaning
            if isinstance(value, str):
                phone = re.sub(r'[^\d\s\-\(\)\+]', '', value)
                if phone and len(phone) >= 10:
                    return phone[:20]  # Limit length
            return None
        
        elif field_name == 'email':
            # Email validation
            if isinstance(value, str):
                email = value.lower()
                if '@' in email and '.' in email:
                    return email[:255]  # Limit length
            return None
        
        # Default: return as string
        return str(value) if value else None
    
    @classmethod
    def _parse_date(cls, date_value: Any) -> Optional[date]:
        """
        Parse date from various formats.
        
        Args:
            date_value: Date in various formats
        
        Returns:
            Parsed date or None
        """
        if not date_value:
            return None
        
        if isinstance(date_value, date):
            return date_value
        
        if isinstance(date_value, datetime):
            return date_value.date()
        
        if isinstance(date_value, str):
            # Try different date formats
            formats = [
                '%Y-%m-%dT%H:%M:%S.%f',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%d',
                '%m/%d/%Y',
                '%m-%d-%Y'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_value, fmt).date()
                except ValueError:
                    continue
        
        return None
    
    @classmethod
    def _extract_cargo_carried(cls, record: Dict[str, Any]) -> Optional[List[str]]:
        """
        Extract cargo carried from various fields.
        
        Args:
            record: FMCSA record
        
        Returns:
            List of cargo types or None
        """
        cargo_types = []
        
        # Check various cargo fields
        cargo_fields = [
            'cargo_carried_1', 'cargo_carried_2', 'cargo_carried_3', 'cargo_carried_4',
            'cargo_carried_5', 'cargo_carried_6', 'cargo_carried_7', 'cargo_carried_8'
        ]
        
        for field in cargo_fields:
            if field in record and record[field]:
                cargo = str(record[field]).strip()
                if cargo and cargo.upper() not in ['NULL', 'NONE', 'N/A']:
                    cargo_types.append(cargo)
        
        return cargo_types if cargo_types else None


class IngestionPipeline:
    """Main ingestion pipeline for FMCSA data."""
    
    def __init__(
        self,
        fmcsa_client: Optional[FMCSAClient] = None,
        batch_size: int = 1000,
        max_errors: int = 100
    ):
        """
        Initialize ingestion pipeline.
        
        Args:
            fmcsa_client: FMCSA API client instance
            batch_size: Number of records to process at once
            max_errors: Maximum errors before stopping
        """
        self.fmcsa_client = fmcsa_client or FMCSAClient()
        self.batch_size = batch_size
        self.max_errors = max_errors
        self.normalizer = CarrierDataNormalizer()
        self.stats = None
    
    async def run_full_ingestion(
        self,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> IngestionStats:
        """
        Run full ingestion of all FMCSA carriers.
        
        Args:
            progress_callback: Callback for progress updates(current, total)
        
        Returns:
            Ingestion statistics
        """
        logger.info("Starting full FMCSA data ingestion...")
        self.stats = IngestionStats(start_time=datetime.now())
        
        try:
            # Ensure database is initialized
            await db_pool.initialize()
            
            # Create partition for current month if needed
            await create_partition_if_needed(datetime.now())
            
            # Process all carriers in batches
            batch_buffer = []
            
            async for api_batch in self.fmcsa_client.fetch_all(
                batch_size=self.fmcsa_client.MAX_RECORDS_PER_REQUEST,
                progress_callback=progress_callback
            ):
                self.stats.total_fetched += len(api_batch)
                
                # Process each record
                for record in api_batch:
                    try:
                        # Normalize data
                        normalized = self.normalizer.normalize(record)
                        batch_buffer.append(normalized)
                        
                        # Process batch when buffer is full
                        if len(batch_buffer) >= self.batch_size:
                            await self._process_batch(batch_buffer)
                            batch_buffer = []
                        
                    except Exception as e:
                        self.stats.total_errors += 1
                        self.stats.error_records.append({
                            "usdot_number": record.get("usdot_number"),
                            "error": str(e),
                            "error_type": type(e).__name__
                        })
                        
                        if self.stats.total_errors >= self.max_errors:
                            logger.error(f"Maximum errors ({self.max_errors}) reached. Stopping ingestion.")
                            break
                
                # Check if we should stop due to errors
                if self.stats.total_errors >= self.max_errors:
                    break
            
            # Process remaining records
            if batch_buffer:
                await self._process_batch(batch_buffer)
            
            # Refresh statistics
            await refresh_statistics()
            
            self.stats.end_time = datetime.now()
            self._log_statistics()
            
            return self.stats
            
        except Exception as e:
            logger.error(f"Ingestion failed: {e}")
            self.stats.end_time = datetime.now()
            raise
    
    async def run_incremental_update(
        self,
        since_date: datetime,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> IngestionStats:
        """
        Run incremental update for records modified since date.
        
        Args:
            since_date: Update records modified after this date
            progress_callback: Progress callback
        
        Returns:
            Ingestion statistics
        """
        logger.info(f"Starting incremental update since {since_date}")
        self.stats = IngestionStats(start_time=datetime.now())
        
        try:
            await db_pool.initialize()
            
            batch_buffer = []
            
            async for api_batch in self.fmcsa_client.fetch_updates(
                since_date=since_date,
                batch_size=self.fmcsa_client.MAX_RECORDS_PER_REQUEST
            ):
                self.stats.total_fetched += len(api_batch)
                
                for record in api_batch:
                    try:
                        normalized = self.normalizer.normalize(record)
                        batch_buffer.append(normalized)
                        
                        if len(batch_buffer) >= self.batch_size:
                            await self._process_batch(batch_buffer, is_update=True)
                            batch_buffer = []
                        
                    except Exception as e:
                        self.stats.total_errors += 1
                        logger.error(f"Error processing record: {e}")
            
            if batch_buffer:
                await self._process_batch(batch_buffer, is_update=True)
            
            await refresh_statistics()
            
            self.stats.end_time = datetime.now()
            self._log_statistics()
            
            return self.stats
            
        except Exception as e:
            logger.error(f"Incremental update failed: {e}")
            self.stats.end_time = datetime.now()
            raise
    
    async def _process_batch(
        self,
        records: List[Dict[str, Any]],
        is_update: bool = False
    ):
        """
        Process a batch of normalized records.
        
        Args:
            records: List of normalized carrier records
            is_update: Whether this is an update operation
        """
        if not records:
            return
        
        try:
            async with db_pool.acquire() as conn:
                # Prepare values for insertion
                values = []
                columns = [
                    'usdot_number', 'legal_name', 'dba_name',
                    'physical_address', 'physical_city', 'physical_state', 'physical_zip', 'physical_country',
                    'mailing_address', 'mailing_city', 'mailing_state', 'mailing_zip',
                    'telephone', 'fax', 'email',
                    'mcs_150_date', 'mcs_150_mileage', 'entity_type', 'operating_status', 'out_of_service_date',
                    'power_units', 'drivers', 'carrier_operation', 'cargo_carried',
                    'liability_insurance_date', 'liability_insurance_amount',
                    'cargo_insurance_date', 'cargo_insurance_amount',
                    'bond_insurance_date', 'bond_insurance_amount',
                    'hazmat_flag', 'hazmat_placardable',
                    'safety_rating', 'safety_rating_date', 'safety_review_date',
                    'raw_data'
                ]
                
                for record in records:
                    row = []
                    for col in columns:
                        value = record.get(col)
                        # Convert lists to PostgreSQL array format
                        if isinstance(value, list):
                            value = value
                        row.append(value)
                    values.append(tuple(row))
                
                # Use COPY for best performance with large batches
                if len(records) > 100:
                    # For large batches, use COPY
                    await conn.copy_records_to_table(
                        'carriers',
                        records=values,
                        columns=columns
                    )
                    self.stats.total_inserted += len(records)
                else:
                    # For smaller batches, use INSERT with ON CONFLICT
                    placeholders = ','.join(
                        f"({','.join(f'${i+j*len(columns)+1}' for i in range(len(columns)))})"
                        for j in range(len(records))
                    )
                    
                    query = f"""
                        INSERT INTO carriers ({','.join(columns)})
                        VALUES {placeholders}
                        ON CONFLICT (usdot_number) DO UPDATE SET
                            legal_name = EXCLUDED.legal_name,
                            dba_name = EXCLUDED.dba_name,
                            physical_address = EXCLUDED.physical_address,
                            physical_city = EXCLUDED.physical_city,
                            physical_state = EXCLUDED.physical_state,
                            entity_type = EXCLUDED.entity_type,
                            operating_status = EXCLUDED.operating_status,
                            power_units = EXCLUDED.power_units,
                            drivers = EXCLUDED.drivers,
                            liability_insurance_date = EXCLUDED.liability_insurance_date,
                            liability_insurance_amount = EXCLUDED.liability_insurance_amount,
                            updated_at = CURRENT_TIMESTAMP,
                            raw_data = EXCLUDED.raw_data
                    """
                    
                    # Flatten values for query
                    flat_values = []
                    for row in values:
                        flat_values.extend(row)
                    
                    result = await conn.execute(query, *flat_values)
                    
                    # Parse result to count inserts vs updates
                    if result:
                        parts = result.split()
                        if parts[0] == 'INSERT':
                            count = int(parts[2])
                            self.stats.total_inserted += count
                        elif parts[0] == 'UPDATE':
                            self.stats.total_updated += int(parts[1])
                
                logger.debug(f"Processed batch of {len(records)} records")
                
        except Exception as e:
            logger.error(f"Error processing batch: {e}")
            self.stats.total_errors += len(records)
            raise
    
    def _log_statistics(self):
        """Log ingestion statistics."""
        if not self.stats:
            return
        
        logger.info("=" * 50)
        logger.info("Ingestion Statistics")
        logger.info("=" * 50)
        logger.info(f"Duration: {self.stats.duration_seconds/60:.1f} minutes")
        logger.info(f"Total fetched: {self.stats.total_fetched:,}")
        logger.info(f"Total inserted: {self.stats.total_inserted:,}")
        logger.info(f"Total updated: {self.stats.total_updated:,}")
        logger.info(f"Total errors: {self.stats.total_errors:,}")
        logger.info(f"Success rate: {self.stats.success_rate:.1f}%")
        
        if self.stats.total_fetched > 0 and self.stats.duration_seconds > 0:
            rate = self.stats.total_fetched / self.stats.duration_seconds
            logger.info(f"Processing rate: {rate:.0f} records/sec")


async def test_pipeline():
    """Test ingestion pipeline with small sample."""
    logging.basicConfig(level=logging.INFO)
    
    pipeline = IngestionPipeline(batch_size=100)
    
    # Test with first 1000 records
    logger.info("Testing ingestion pipeline with 1000 records...")
    
    def progress(current, total):
        print(f"Progress: {current}/{total} ({current/total*100:.1f}%)")
    
    # Override fetch_all to limit records for testing
    original_fetch_all = pipeline.fmcsa_client.fetch_all
    
    async def limited_fetch_all(*args, **kwargs):
        count = 0
        async for batch in original_fetch_all(*args, **kwargs):
            yield batch[:min(len(batch), 1000 - count)]
            count += len(batch)
            if count >= 1000:
                break
    
    pipeline.fmcsa_client.fetch_all = limited_fetch_all
    
    stats = await pipeline.run_full_ingestion(progress_callback=progress)
    
    print(f"\nTest completed: {stats.to_dict()}")


if __name__ == "__main__":
    asyncio.run(test_pipeline())