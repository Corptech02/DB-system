"""
Initial data load script for FMCSA database.
Run this once to populate the database with carrier data.
"""

import asyncio
import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from fmcsa_system.database import initialize_database, close_database
from fmcsa_system.ingestion.fmcsa_client import FMCSAClient
from fmcsa_system.ingestion.ingestion_pipeline import IngestionPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def run_initial_load(limit: int = None, batch_size: int = 1000):
    """
    Run initial data load from FMCSA API.
    
    Args:
        limit: Optional limit on number of records to fetch (for testing)
        batch_size: Number of records to process in each batch
    """
    logger.info("=" * 60)
    logger.info("FMCSA Initial Data Load")
    logger.info("=" * 60)
    
    start_time = datetime.now()
    
    try:
        # Initialize database
        logger.info("Initializing database connection...")
        await initialize_database()
        
        # Create client and pipeline
        client = FMCSAClient()
        pipeline = IngestionPipeline(
            fmcsa_client=client,
            batch_size=batch_size
        )
        
        # Get total count
        if limit:
            logger.info(f"Running limited load: {limit} records")
            total_count = limit
        else:
            logger.info("Getting total carrier count from FMCSA API...")
            total_count = await client.get_total_count()
            logger.info(f"Total carriers available: {total_count:,}")
        
        # Confirm with user for full load
        if not limit and total_count > 100000:
            logger.warning(f"This will load {total_count:,} records and may take 1-2 hours.")
            response = input("Continue? (y/n): ")
            if response.lower() != 'y':
                logger.info("Load cancelled by user")
                return
        
        # Progress callback
        def progress_callback(current: int, total: int):
            percent = (current / total) * 100
            elapsed = (datetime.now() - start_time).total_seconds()
            rate = current / elapsed if elapsed > 0 else 0
            eta = (total - current) / rate if rate > 0 else 0
            
            logger.info(
                f"Progress: {current:,}/{total:,} ({percent:.1f}%) | "
                f"Rate: {rate:.0f} records/sec | "
                f"ETA: {eta/60:.1f} minutes"
            )
        
        # Run ingestion
        logger.info("Starting data ingestion...")
        stats = await pipeline.run_full_ingestion(
            progress_callback=progress_callback,
            limit=limit
        )
        
        # Print results
        duration = (datetime.now() - start_time).total_seconds()
        logger.info("=" * 60)
        logger.info("Load Complete!")
        logger.info(f"Total records fetched: {stats.total_fetched:,}")
        logger.info(f"Records inserted: {stats.total_inserted:,}")
        logger.info(f"Records updated: {stats.total_updated:,}")
        logger.info(f"Errors: {stats.total_errors:,}")
        logger.info(f"Duration: {duration/60:.1f} minutes")
        logger.info(f"Average rate: {stats.total_fetched/duration:.0f} records/sec")
        logger.info("=" * 60)
        
    except KeyboardInterrupt:
        logger.warning("Load interrupted by user")
    except Exception as e:
        logger.error(f"Load failed: {e}", exc_info=True)
        raise
    finally:
        # Clean up
        await close_database()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Load FMCSA carrier data into database"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of records to fetch (for testing)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Number of records to process in each batch (default: 1000)"
    )
    
    args = parser.parse_args()
    
    # Run async load
    asyncio.run(run_initial_load(
        limit=args.limit,
        batch_size=args.batch_size
    ))


if __name__ == "__main__":
    main()