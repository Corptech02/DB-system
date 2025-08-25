#!/usr/bin/env python
"""
Standalone script to import FMCSA carrier data.
Demonstrates the ingestion pipeline with progress tracking.

Usage:
    python import_script.py --limit 10000  # Import first 10k records
    python import_script.py --state CA     # Import California carriers
    python import_script.py --full         # Import all 2.2M+ records (takes ~90 min)
"""

import sys
import os
import asyncio
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion.fmcsa_client import FMCSAClient
from ingestion.ingestion_pipeline import IngestionPipeline, IngestionStats
from database import initialize_database, test_connection, close_database


class ProgressBar:
    """Simple progress bar for console output."""
    
    def __init__(self, total: int, width: int = 50):
        self.total = total
        self.width = width
        self.current = 0
        self.start_time = datetime.now()
    
    def update(self, current: int, estimated_total: int = None):
        """Update progress bar."""
        self.current = current
        if estimated_total:
            self.total = estimated_total
        
        # Calculate progress
        if self.total > 0:
            progress = min(self.current / self.total, 1.0)
        else:
            progress = 0
        
        # Calculate time elapsed and ETA
        elapsed = (datetime.now() - self.start_time).total_seconds()
        if progress > 0 and progress < 1:
            eta = elapsed * (1 - progress) / progress
            eta_str = f"ETA: {int(eta/60)}m {int(eta%60)}s"
        else:
            eta_str = ""
        
        # Create progress bar
        filled = int(self.width * progress)
        bar = "█" * filled + "░" * (self.width - filled)
        
        # Print progress
        print(f"\r[{bar}] {progress*100:.1f}% | {self.current:,}/{self.total:,} records | {eta_str}", 
              end="", flush=True)
    
    def finish(self):
        """Mark progress as complete."""
        self.update(self.total)
        print()  # New line


async def import_limited(limit: int):
    """
    Import a limited number of records for testing.
    
    Args:
        limit: Maximum number of records to import
    """
    print(f"Importing first {limit:,} FMCSA carrier records...")
    
    # Initialize components
    client = FMCSAClient()
    pipeline = IngestionPipeline(fmcsa_client=client, batch_size=500)
    
    # Create progress bar
    progress_bar = ProgressBar(total=limit)
    
    # Override fetch_all to limit records
    original_fetch_all = client.fetch_all
    
    async def limited_fetch_all(*args, **kwargs):
        count = 0
        async for batch in original_fetch_all(*args, **kwargs):
            remaining = limit - count
            if remaining <= 0:
                break
            
            batch_to_yield = batch[:remaining]
            yield batch_to_yield
            count += len(batch_to_yield)
            
            if count >= limit:
                break
    
    client.fetch_all = limited_fetch_all
    
    # Run ingestion
    stats = await pipeline.run_full_ingestion(
        progress_callback=lambda c, t: progress_bar.update(c, min(t, limit))
    )
    
    progress_bar.finish()
    
    return stats


async def import_by_state(state_code: str):
    """
    Import carriers for a specific state.
    
    Args:
        state_code: Two-letter state code
    """
    print(f"Importing FMCSA carriers for state: {state_code.upper()}")
    
    # Initialize components
    client = FMCSAClient()
    pipeline = IngestionPipeline(fmcsa_client=client, batch_size=500)
    
    # Get count for state
    where_clause = f"phy_state = '{state_code.upper()}'"
    total_count = await client.get_total_count(where=where_clause)
    print(f"Found {total_count:,} carriers in {state_code.upper()}")
    
    # Create progress bar
    progress_bar = ProgressBar(total=total_count)
    
    # Fetch state-specific records
    records_processed = 0
    batch_buffer = []
    
    async for batch in client.fetch_all(
        where=where_clause,
        progress_callback=lambda c, t: progress_bar.update(c, t)
    ):
        for record in batch:
            try:
                normalized = pipeline.normalizer.normalize(record)
                batch_buffer.append(normalized)
                
                if len(batch_buffer) >= pipeline.batch_size:
                    await pipeline._process_batch(batch_buffer)
                    batch_buffer = []
                
                records_processed += 1
                
            except Exception as e:
                logging.error(f"Error processing record: {e}")
    
    # Process remaining records
    if batch_buffer:
        await pipeline._process_batch(batch_buffer)
    
    progress_bar.finish()
    
    # Create stats
    stats = IngestionStats(start_time=pipeline.stats.start_time if pipeline.stats else datetime.now())
    stats.end_time = datetime.now()
    stats.total_fetched = records_processed
    stats.total_inserted = pipeline.stats.total_inserted if pipeline.stats else records_processed
    
    return stats


async def import_full():
    """Import all FMCSA carrier records (2.2M+)."""
    print("Starting FULL FMCSA data import (2.2M+ records)")
    print("This will take approximately 60-90 minutes...")
    
    response = input("Are you sure you want to continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Import cancelled.")
        return None
    
    # Initialize components
    client = FMCSAClient()
    pipeline = IngestionPipeline(fmcsa_client=client, batch_size=1000)
    
    # Get total count
    total_count = await client.get_total_count()
    print(f"Total carriers to import: {total_count:,}")
    
    # Create progress bar
    progress_bar = ProgressBar(total=total_count)
    
    # Run full ingestion
    stats = await pipeline.run_full_ingestion(
        progress_callback=lambda c, t: progress_bar.update(c, t)
    )
    
    progress_bar.finish()
    
    return stats


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Import FMCSA carrier data into PostgreSQL database"
    )
    
    # Import options (mutually exclusive)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--limit",
        type=int,
        metavar="N",
        help="Import only first N records (for testing)"
    )
    group.add_argument(
        "--state",
        type=str,
        metavar="XX",
        help="Import carriers for specific state (2-letter code)"
    )
    group.add_argument(
        "--full",
        action="store_true",
        help="Import all 2.2M+ carrier records"
    )
    
    # Other options
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--test-connection",
        action="store_true",
        help="Test database connection and exit"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("import.log"),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize database
        logger.info("Initializing database connection...")
        await initialize_database()
        
        # Test connection
        if args.test_connection or True:  # Always test
            logger.info("Testing database connection...")
            if not await test_connection():
                logger.error("Database connection test failed!")
                print("\n❌ Database connection failed. Please check your configuration.")
                print("Make sure:")
                print("1. PostgreSQL is running")
                print("2. Database 'fmcsa_db' exists")
                print("3. Schema is loaded (psql fmcsa_db < database/schema.sql)")
                print("4. DATABASE_URL is correctly set in .env")
                return
            
            if args.test_connection:
                print("✅ Database connection successful!")
                return
        
        # Run import based on arguments
        stats = None
        start_time = datetime.now()
        
        print("\n" + "="*60)
        print("FMCSA DATA IMPORT")
        print("="*60)
        
        if args.limit:
            stats = await import_limited(args.limit)
        elif args.state:
            stats = await import_by_state(args.state)
        elif args.full:
            stats = await import_full()
        
        # Print results
        if stats:
            duration = (datetime.now() - start_time).total_seconds()
            
            print("\n" + "="*60)
            print("IMPORT COMPLETED")
            print("="*60)
            print(f"Duration: {duration/60:.1f} minutes")
            print(f"Records fetched: {stats.total_fetched:,}")
            print(f"Records inserted: {stats.total_inserted:,}")
            print(f"Records updated: {stats.total_updated:,}")
            print(f"Errors: {stats.total_errors:,}")
            
            if stats.total_fetched > 0:
                print(f"Success rate: {stats.success_rate:.1f}%")
                print(f"Processing rate: {stats.total_fetched/duration:.0f} records/sec")
            
            if stats.total_errors > 0:
                print(f"\n⚠️  {stats.total_errors} errors occurred during import.")
                print("Check import.log for details.")
        
    except KeyboardInterrupt:
        print("\n\nImport cancelled by user.")
    except Exception as e:
        logger.error(f"Import failed: {e}", exc_info=True)
        print(f"\n❌ Import failed: {e}")
        print("Check import.log for details.")
    finally:
        # Close database connection
        await close_database()


if __name__ == "__main__":
    asyncio.run(main())