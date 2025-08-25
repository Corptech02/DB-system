"""
Fetch ALL 2.2M+ FMCSA carriers from data.transportation.gov
Optimized for bulk downloading with progress tracking and resume capability.
"""

import aiohttp
import asyncio
import json
import os
from datetime import datetime
from typing import List, Dict, Any
import pickle

class BulkFMCSAFetcher:
    """Efficiently fetch all FMCSA carrier data."""
    
    def __init__(self):
        self.base_url = "https://data.transportation.gov/resource/az4n-8mr2.json"
        self.batch_size = 50000  # Max allowed by Socrata API
        self.carriers = []
        self.checkpoint_file = "fetch_checkpoint.pkl"
        self.output_dir = "carrier_data"
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
    
    async def get_total_count(self, session: aiohttp.ClientSession) -> int:
        """Get total number of carriers available."""
        params = {
            "$select": "count(*)",
        }
        
        try:
            async with session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data and len(data) > 0:
                        return int(data[0].get('count', 0))
        except Exception as e:
            print(f"Error getting count: {e}")
        
        # Fallback estimate
        return 2200000
    
    async def fetch_batch(self, session: aiohttp.ClientSession, offset: int) -> List[Dict]:
        """Fetch a batch of carriers."""
        params = {
            "$limit": self.batch_size,
            "$offset": offset,
            "$order": "dot_number"
        }
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with session.get(self.base_url, params=params, timeout=30) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 429:  # Rate limited
                        wait_time = 2 ** attempt
                        print(f"Rate limited. Waiting {wait_time} seconds...")
                        await asyncio.sleep(wait_time)
                    else:
                        print(f"Error: HTTP {response.status} at offset {offset}")
                        return []
            except asyncio.TimeoutError:
                print(f"Timeout at offset {offset}, attempt {attempt + 1}")
                await asyncio.sleep(1)
            except Exception as e:
                print(f"Error at offset {offset}: {e}")
                await asyncio.sleep(1)
        
        return []
    
    def save_checkpoint(self, offset: int, total_fetched: int):
        """Save progress checkpoint."""
        checkpoint = {
            'offset': offset,
            'total_fetched': total_fetched,
            'timestamp': datetime.now()
        }
        with open(self.checkpoint_file, 'wb') as f:
            pickle.dump(checkpoint, f)
    
    def load_checkpoint(self):
        """Load progress checkpoint if it exists."""
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, 'rb') as f:
                    checkpoint = pickle.load(f)
                print(f"Resuming from checkpoint: {checkpoint['total_fetched']:,} carriers fetched")
                return checkpoint['offset'], checkpoint['total_fetched']
            except:
                pass
        return 0, 0
    
    def save_batch_to_file(self, batch: List[Dict], batch_num: int):
        """Save batch to individual file for safety."""
        filename = os.path.join(self.output_dir, f"batch_{batch_num:05d}.json")
        with open(filename, 'w') as f:
            json.dump(batch, f)
    
    async def fetch_all(self):
        """Fetch all carriers with progress tracking and resume capability."""
        print("=" * 70)
        print("FETCHING ALL FMCSA CARRIERS")
        print("=" * 70)
        
        # Check for existing checkpoint
        start_offset, total_fetched = self.load_checkpoint()
        
        # Load any previously fetched data
        if start_offset > 0:
            print("Loading previously fetched data...")
            for i in range(start_offset // self.batch_size):
                batch_file = os.path.join(self.output_dir, f"batch_{i:05d}.json")
                if os.path.exists(batch_file):
                    with open(batch_file, 'r') as f:
                        self.carriers.extend(json.load(f))
            print(f"Loaded {len(self.carriers):,} carriers from previous run")
        
        start_time = datetime.now()
        
        # Configure connection pool for better performance
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=10)
        timeout = aiohttp.ClientTimeout(total=60)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # Get total count
            total_count = await self.get_total_count(session)
            print(f"Total carriers available: {total_count:,}")
            print(f"Batch size: {self.batch_size:,}")
            print(f"Estimated batches: {(total_count // self.batch_size) + 1}")
            print("-" * 70)
            
            offset = start_offset
            batch_num = start_offset // self.batch_size
            consecutive_empty = 0
            
            while offset < total_count:
                # Fetch batch
                batch_start = datetime.now()
                batch = await self.fetch_batch(session, offset)
                
                if not batch:
                    consecutive_empty += 1
                    if consecutive_empty >= 3:
                        print("No more data available")
                        break
                    await asyncio.sleep(1)
                    continue
                
                consecutive_empty = 0
                
                # Save batch to file
                self.save_batch_to_file(batch, batch_num)
                
                # Add to main list
                self.carriers.extend(batch)
                total_fetched += len(batch)
                
                # Progress update
                elapsed = (datetime.now() - start_time).total_seconds()
                rate = (total_fetched - start_offset) / elapsed if elapsed > 0 else 0
                eta_seconds = (total_count - total_fetched) / rate if rate > 0 else 0
                
                print(f"Batch {batch_num:4d} | "
                      f"Fetched: {total_fetched:,}/{total_count:,} "
                      f"({total_fetched/total_count*100:.1f}%) | "
                      f"Rate: {rate:.0f}/sec | "
                      f"ETA: {eta_seconds/60:.1f} min")
                
                # Save checkpoint every 10 batches
                if batch_num % 10 == 0:
                    self.save_checkpoint(offset + self.batch_size, total_fetched)
                
                # Move to next batch
                offset += self.batch_size
                batch_num += 1
                
                # Small delay to be nice to the API
                await asyncio.sleep(0.1)
        
        # Final save
        print("-" * 70)
        print("Saving complete dataset...")
        
        # Save full dataset
        output_file = "all_carriers.json"
        with open(output_file, 'w') as f:
            json.dump(self.carriers, f)
        
        # Save compressed version
        import gzip
        with gzip.open("all_carriers.json.gz", 'wt') as f:
            json.dump(self.carriers, f)
        
        # Clean up checkpoint
        if os.path.exists(self.checkpoint_file):
            os.remove(self.checkpoint_file)
        
        total_time = (datetime.now() - start_time).total_seconds()
        
        print("=" * 70)
        print(f"✓ COMPLETE!")
        print(f"✓ Total carriers fetched: {len(self.carriers):,}")
        print(f"✓ Time taken: {total_time/60:.1f} minutes")
        print(f"✓ Average rate: {len(self.carriers)/total_time:.0f} carriers/sec")
        print(f"✓ Data saved to: {output_file}")
        print(f"✓ Compressed data: all_carriers.json.gz")
        print("=" * 70)


async def main():
    """Main function."""
    fetcher = BulkFMCSAFetcher()
    
    print("This will download ALL 2.2M+ FMCSA carriers.")
    print("Estimated time: 45-90 minutes")
    print("Estimated size: ~1-2 GB")
    print("")
    
    response = input("Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled.")
        return
    
    await fetcher.fetch_all()


if __name__ == "__main__":
    asyncio.run(main())