"""
FMCSA SODA API client with pagination support.
Handles fetching carrier data from data.transportation.gov with retry logic.
"""

import os
import asyncio
import logging
from typing import List, Dict, Any, Optional, AsyncIterator
from datetime import datetime
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class FMCSAClient:
    """
    Client for FMCSA Company Census API using SODA (Socrata Open Data API).
    Handles pagination, rate limiting, and retry logic for 2.2M+ records.
    """
    
    BASE_URL = "https://data.transportation.gov/resource/az4n-8mr2.json"
    MAX_RECORDS_PER_REQUEST = 50000  # SODA API limit
    DEFAULT_TIMEOUT = 30  # seconds
    
    def __init__(
        self,
        app_token: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        retry_backoff: float = 2.0
    ):
        """
        Initialize FMCSA API client.
        
        Args:
            app_token: Socrata app token (recommended to avoid rate limits)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay between retries
            retry_backoff: Backoff multiplier for retries
        """
        self.app_token = app_token or os.getenv("SODA_APP_TOKEN")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.retry_backoff = retry_backoff
        
        # Setup headers
        self.headers = {}
        if self.app_token:
            self.headers["X-App-Token"] = self.app_token
            logger.info("Using SODA app token for API requests")
        else:
            logger.warning("No SODA app token provided. May hit rate limits.")
        
        # Track statistics
        self.stats = {
            "total_requests": 0,
            "total_records": 0,
            "failed_requests": 0,
            "start_time": None,
            "end_time": None
        }
    
    async def fetch_batch(
        self,
        limit: int = MAX_RECORDS_PER_REQUEST,
        offset: int = 0,
        where: Optional[str] = None,
        select: Optional[str] = None,
        order: str = "usdot_number"
    ) -> List[Dict[str, Any]]:
        """
        Fetch a batch of records from FMCSA API.
        
        Args:
            limit: Number of records to fetch (max 50000)
            offset: Number of records to skip
            where: SoQL WHERE clause for filtering
            select: Comma-separated list of fields to return
            order: Field to order by (important for consistent pagination)
        
        Returns:
            List of carrier records
        """
        # Ensure limit doesn't exceed API maximum
        limit = min(limit, self.MAX_RECORDS_PER_REQUEST)
        
        # Build query parameters
        params = {
            "$limit": limit,
            "$offset": offset,
            "$order": order
        }
        
        if where:
            params["$where"] = where
        
        if select:
            params["$select"] = select
        
        # Retry logic with exponential backoff
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(
                        self.BASE_URL,
                        params=params,
                        headers=self.headers
                    )
                    
                    # Check for rate limiting
                    if response.status_code == 429:
                        retry_after = int(response.headers.get("Retry-After", 60))
                        logger.warning(f"Rate limited. Waiting {retry_after} seconds...")
                        await asyncio.sleep(retry_after)
                        continue
                    
                    response.raise_for_status()
                    
                    # Update statistics
                    self.stats["total_requests"] += 1
                    data = response.json()
                    self.stats["total_records"] += len(data)
                    
                    logger.debug(f"Fetched {len(data)} records (offset: {offset})")
                    return data
                    
            except httpx.TimeoutException:
                logger.warning(f"Request timeout (attempt {attempt + 1}/{self.max_retries})")
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
                if e.response.status_code >= 500:
                    # Server error - retry
                    pass
                else:
                    # Client error - don't retry
                    self.stats["failed_requests"] += 1
                    raise
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                self.stats["failed_requests"] += 1
                if attempt == self.max_retries - 1:
                    raise
            
            # Wait before retry with exponential backoff
            if attempt < self.max_retries - 1:
                delay = self.retry_delay * (self.retry_backoff ** attempt)
                logger.info(f"Retrying in {delay:.1f} seconds...")
                await asyncio.sleep(delay)
        
        # If we get here, all retries failed
        self.stats["failed_requests"] += 1
        raise Exception(f"Failed to fetch data after {self.max_retries} attempts")
    
    async def fetch_all(
        self,
        batch_size: int = MAX_RECORDS_PER_REQUEST,
        where: Optional[str] = None,
        select: Optional[str] = None,
        progress_callback: Optional[callable] = None,
        rate_limit_delay: float = 0.5
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """
        Fetch all records from FMCSA API with pagination.
        
        Args:
            batch_size: Records per batch (max 50000)
            where: SoQL WHERE clause for filtering
            select: Fields to return
            progress_callback: Callback function(current, estimated_total)
            rate_limit_delay: Delay between requests to be respectful
        
        Yields:
            Batches of carrier records
        """
        self.stats["start_time"] = datetime.now()
        offset = 0
        estimated_total = 2200000  # Approximate total carriers
        
        # Get actual count if filtering
        if where:
            count_data = await self.fetch_batch(
                limit=1,
                offset=0,
                where=where,
                select="COUNT(*) as count"
            )
            if count_data:
                estimated_total = int(count_data[0].get("count", estimated_total))
                logger.info(f"Found {estimated_total} matching records")
        
        while True:
            # Fetch batch
            batch = await self.fetch_batch(
                limit=batch_size,
                offset=offset,
                where=where,
                select=select
            )
            
            if not batch:
                # No more data
                break
            
            yield batch
            
            # Update progress
            offset += len(batch)
            if progress_callback:
                progress_callback(offset, estimated_total)
            
            # Log progress
            if offset % 100000 == 0:
                elapsed = (datetime.now() - self.stats["start_time"]).total_seconds()
                rate = offset / elapsed if elapsed > 0 else 0
                eta = (estimated_total - offset) / rate if rate > 0 else 0
                logger.info(
                    f"Progress: {offset:,}/{estimated_total:,} records "
                    f"({offset/estimated_total*100:.1f}%) - "
                    f"Rate: {rate:.0f} records/sec - ETA: {eta/60:.1f} min"
                )
            
            # Check if we got less than requested (indicates last batch)
            if len(batch) < batch_size:
                break
            
            # Rate limiting - be respectful to the API
            await asyncio.sleep(rate_limit_delay)
        
        self.stats["end_time"] = datetime.now()
        self._log_statistics()
    
    async def fetch_updates(
        self,
        since_date: datetime,
        batch_size: int = MAX_RECORDS_PER_REQUEST
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """
        Fetch only records updated since a specific date.
        
        Args:
            since_date: Fetch records updated after this date
            batch_size: Records per batch
        
        Yields:
            Batches of updated carrier records
        """
        # Format date for SoQL query
        date_str = since_date.strftime("%Y-%m-%dT%H:%M:%S")
        where_clause = f"mcs_150_date > '{date_str}'"
        
        logger.info(f"Fetching records updated since {date_str}")
        
        async for batch in self.fetch_all(
            batch_size=batch_size,
            where=where_clause
        ):
            yield batch
    
    async def fetch_by_state(
        self,
        state_code: str,
        batch_size: int = MAX_RECORDS_PER_REQUEST
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """
        Fetch carriers for a specific state.
        
        Args:
            state_code: Two-letter state code
            batch_size: Records per batch
        
        Yields:
            Batches of carrier records for the state
        """
        where_clause = f"phy_state = '{state_code.upper()}'"
        
        logger.info(f"Fetching carriers for state: {state_code}")
        
        async for batch in self.fetch_all(
            batch_size=batch_size,
            where=where_clause
        ):
            yield batch
    
    async def fetch_single(self, usdot_number: int) -> Optional[Dict[str, Any]]:
        """
        Fetch a single carrier by USDOT number.
        
        Args:
            usdot_number: USDOT number to fetch
        
        Returns:
            Carrier record or None if not found
        """
        where_clause = f"usdot_number = {usdot_number}"
        
        batch = await self.fetch_batch(
            limit=1,
            offset=0,
            where=where_clause
        )
        
        return batch[0] if batch else None
    
    async def get_total_count(self, where: Optional[str] = None) -> int:
        """
        Get total count of records matching criteria.
        
        Args:
            where: Optional SoQL WHERE clause
        
        Returns:
            Total count of matching records
        """
        result = await self.fetch_batch(
            limit=1,
            offset=0,
            where=where,
            select="COUNT(*) as count"
        )
        
        return int(result[0]["count"]) if result else 0
    
    def _log_statistics(self):
        """Log ingestion statistics."""
        if not self.stats["start_time"] or not self.stats["end_time"]:
            return
        
        duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
        
        logger.info("=" * 50)
        logger.info("FMCSA API Client Statistics")
        logger.info("=" * 50)
        logger.info(f"Total requests: {self.stats['total_requests']:,}")
        logger.info(f"Total records: {self.stats['total_records']:,}")
        logger.info(f"Failed requests: {self.stats['failed_requests']}")
        logger.info(f"Duration: {duration/60:.1f} minutes")
        
        if duration > 0:
            logger.info(f"Average rate: {self.stats['total_records']/duration:.0f} records/sec")
            logger.info(f"Average batch size: {self.stats['total_records']/self.stats['total_requests']:.0f}")


async def test_client():
    """Test FMCSA client with a small sample."""
    client = FMCSAClient()
    
    # Test fetching a small batch
    logger.info("Testing FMCSA API client...")
    
    try:
        # Fetch first 10 records
        batch = await client.fetch_batch(limit=10)
        logger.info(f"Successfully fetched {len(batch)} records")
        
        if batch:
            # Show sample record structure
            sample = batch[0]
            logger.info(f"Sample record fields: {list(sample.keys())}")
            logger.info(f"Sample USDOT: {sample.get('usdot_number')}")
            logger.info(f"Sample Name: {sample.get('legal_name')}")
        
        # Test count
        total = await client.get_total_count()
        logger.info(f"Total records in database: {total:,}")
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Run test
    asyncio.run(test_client())