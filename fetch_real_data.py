"""
Fetch REAL FMCSA carrier data from the official government API.
This uses the actual Socrata Open Data API endpoint you provided.
"""

import aiohttp
import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import os

class RealFMCSAFetcher:
    """Fetches real FMCSA carrier data from data.transportation.gov"""
    
    def __init__(self):
        # The real FMCSA Socrata API endpoint
        self.base_url = "https://data.transportation.gov/resource/az4n-8mr2.json"
        self.max_limit = 50000  # Socrata max limit per request
        self.carriers = []
        
    async def fetch_batch(self, session: aiohttp.ClientSession, limit: int, offset: int) -> List[Dict]:
        """Fetch a batch of carriers from the API."""
        params = {
            "$limit": limit,
            "$offset": offset,
            "$order": "dot_number"  # Order by DOT number for consistent pagination
        }
        
        try:
            async with session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"Fetched {len(data)} records (offset: {offset})")
                    return data
                else:
                    print(f"Error: HTTP {response.status} at offset {offset}")
                    return []
        except Exception as e:
            print(f"Error fetching batch at offset {offset}: {e}")
            return []
    
    async def fetch_all(self, max_records: Optional[int] = None):
        """
        Fetch all carrier records from the API.
        
        Args:
            max_records: Maximum number of records to fetch (None for all)
        """
        print("=" * 60)
        print("FETCHING REAL FMCSA CARRIER DATA")
        print("=" * 60)
        print(f"API Endpoint: {self.base_url}")
        print(f"Batch size: {self.max_limit}")
        
        if max_records:
            print(f"Limiting to {max_records:,} records")
        else:
            print("Fetching ALL records (this may take a while...)")
        
        print("-" * 60)
        
        offset = 0
        total_fetched = 0
        start_time = datetime.now()
        
        async with aiohttp.ClientSession() as session:
            while True:
                # Calculate batch size
                if max_records:
                    remaining = max_records - total_fetched
                    if remaining <= 0:
                        break
                    batch_size = min(self.max_limit, remaining)
                else:
                    batch_size = self.max_limit
                
                # Fetch batch
                batch = await self.fetch_batch(session, batch_size, offset)
                
                if not batch:
                    # No more data or error occurred
                    break
                
                self.carriers.extend(batch)
                total_fetched += len(batch)
                offset += batch_size
                
                # Progress update
                elapsed = (datetime.now() - start_time).total_seconds()
                rate = total_fetched / elapsed if elapsed > 0 else 0
                print(f"Total fetched: {total_fetched:,} | Rate: {rate:.0f} records/sec")
                
                # If we got less than requested, we've reached the end
                if len(batch) < batch_size:
                    print("Reached end of data")
                    break
                
                # Small delay to be nice to the API
                await asyncio.sleep(0.1)
        
        print("-" * 60)
        print(f"✓ Fetched {len(self.carriers):,} total carriers")
        print(f"✓ Time taken: {(datetime.now() - start_time).total_seconds():.1f} seconds")
        print("=" * 60)
        
        return self.carriers
    
    def save_to_file(self, filename: str = "real_carriers.json"):
        """Save fetched carriers to a JSON file."""
        with open(filename, 'w') as f:
            json.dump(self.carriers, f, indent=2, default=str)
        print(f"Saved {len(self.carriers)} carriers to {filename}")
    
    def get_sample_info(self):
        """Print information about the fetched data."""
        if not self.carriers:
            print("No carriers fetched yet")
            return
        
        print("\nSample carrier record:")
        print(json.dumps(self.carriers[0], indent=2, default=str))
        
        # Get field names
        fields = set()
        for carrier in self.carriers[:100]:  # Check first 100 records
            fields.update(carrier.keys())
        
        print(f"\nAvailable fields ({len(fields)}):")
        for field in sorted(fields):
            print(f"  - {field}")
        
        # State distribution
        states = {}
        for carrier in self.carriers:
            state = carrier.get('phy_state', 'Unknown')
            states[state] = states.get(state, 0) + 1
        
        print(f"\nState distribution (top 10):")
        for state, count in sorted(states.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {state}: {count:,}")


async def main():
    """Main function to fetch real FMCSA data."""
    fetcher = RealFMCSAFetcher()
    
    # Options - uncomment the one you want:
    
    # Option 1: Fetch a small sample for testing (1000 records)
    await fetcher.fetch_all(max_records=1000)
    
    # Option 2: Fetch more data (10,000 records)
    # await fetcher.fetch_all(max_records=10000)
    
    # Option 3: Fetch ALL data (2.2M+ records) - WARNING: This will take 1+ hours!
    # await fetcher.fetch_all()
    
    # Show sample information
    fetcher.get_sample_info()
    
    # Save to file
    fetcher.save_to_file("real_carriers_sample.json")
    
    print("\n✓ Done! Data saved to real_carriers_sample.json")
    print("\nYou can now use this real data in your application!")


if __name__ == "__main__":
    print("FMCSA Real Data Fetcher")
    print("This will fetch actual carrier data from data.transportation.gov")
    print("")
    
    # Run the async fetcher
    asyncio.run(main())