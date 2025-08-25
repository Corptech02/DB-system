#!/usr/bin/env python3
"""
FMCSA Insurance Service
Complete automated insurance data management system
"""

import json
import os
import time
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
from pathlib import Path

# Try to load dotenv if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class FMCSAInsuranceService:
    """Complete automated insurance data management system"""
    
    def __init__(self, webkey: Optional[str] = None):
        self.webkey = webkey or os.getenv("FMCSA_WEBKEY")
        self.qc_base_url = "https://mobile.fmcsa.dot.gov/qc/services"
        self.soda_base_url = "https://data.transportation.gov/resource/7xzn-4j4j.json"
        
        # Cache and queue files
        self.cache_file = Path("li_insurance_cache.json")
        self.pending_file = Path("li_pending_lookups.json")
        self.log_file = Path("insurance_service.log")
        
        # Initialize files
        self._init_files()
    
    def _init_files(self):
        """Initialize required files"""
        if not self.cache_file.exists():
            self.cache_file.write_text("{}")
        if not self.pending_file.exists():
            self.pending_file.write_text("[]")
        
    def get_carrier_from_qcmobile(self, usdot_number: int) -> Optional[Dict[str, Any]]:
        """
        Get carrier data from QCMobile API (requires WebKey)
        """
        if not self.webkey:
            print("No FMCSA WebKey provided. Get one at https://mobile.fmcsa.dot.gov/QCDevsite/")
            return None
            
        url = f"{self.qc_base_url}/carriers/{usdot_number}"
        params = {"webKey": self.webkey}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return self._extract_insurance_from_qcmobile(data)
            else:
                print(f"QCMobile API error: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error fetching from QCMobile: {e}")
            return None
    
    def get_carrier_from_soda(self, usdot_number: int) -> Optional[Dict[str, Any]]:
        """
        Get carrier data from Socrata Open Data API (no key required)
        """
        params = {
            "$limit": 1,
            "$where": f"legal_name IS NOT NULL AND dot_number = '{usdot_number}'"
        }
        
        try:
            response = requests.get(self.soda_base_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data:
                    return self._extract_insurance_from_soda(data[0])
            return None
        except Exception as e:
            print(f"Error fetching from SODA API: {e}")
            return None
    
    def _extract_insurance_from_qcmobile(self, data: Dict) -> Dict[str, Any]:
        """Extract insurance information from QCMobile API response"""
        content = data.get("content", {})
        carrier = content.get("carrier", {})
        insurance = content.get("insurance", {})
        
        return {
            "source": "FMCSA QCMobile API",
            "usdot_number": carrier.get("dotNumber"),
            "legal_name": carrier.get("legalName"),
            "dba_name": carrier.get("dbaName"),
            
            # Insurance Status
            "insurance_on_file": insurance.get("insuranceOnFile"),
            "insurance_required": insurance.get("insuranceRequired"),
            
            # Liability Insurance
            "bipd_required": insurance.get("bipdInsuranceRequired"),
            "bipd_on_file": insurance.get("bipdInsuranceOnFile"),
            "liability_coverage": insurance.get("liabilityCoverage"),
            
            # Cargo Insurance  
            "cargo_required": insurance.get("cargoInsuranceRequired"),
            "cargo_on_file": insurance.get("cargoInsuranceOnFile"),
            "cargo_coverage": insurance.get("cargoCoverage"),
            
            # Bond Insurance
            "bond_required": insurance.get("bondInsuranceRequired"),
            "bond_on_file": insurance.get("bondInsuranceOnFile"),
            "bond_coverage": insurance.get("bondCoverage"),
            
            # Insurance Details (if available)
            "insurance_carrier": insurance.get("insuranceCarrier"),
            "policy_number": insurance.get("policyNumber"),
            "coverage_from": insurance.get("coverageFrom"),
            "coverage_to": insurance.get("coverageTo"),
            
            # Additional carrier info
            "operating_status": carrier.get("statusCode"),
            "entity_type": carrier.get("entityType"),
            "power_units": carrier.get("totalPowerUnits"),
            "out_of_service_date": carrier.get("oosDate"),
            
            "fetched_at": datetime.now().isoformat()
        }
    
    def _extract_insurance_from_soda(self, data: Dict) -> Dict[str, Any]:
        """Extract insurance information from SODA API response"""
        return {
            "source": "FMCSA SODA Open Data API",
            "usdot_number": data.get("dot_number"),
            "legal_name": data.get("legal_name"),
            "dba_name": data.get("dba_name"),
            
            # Note: SODA API has limited insurance fields
            "mcs150_date": data.get("mcs150_date"),
            "mcs150_mileage": data.get("mcs150_mileage"),
            "operating_status": data.get("operating_status"),
            "entity_type": data.get("entity_type"),
            "power_units": data.get("power_units"),
            
            # Basic insurance indicators (if available)
            "insurance_carrier": data.get("insurance_carrier"),
            "insurance_type": data.get("insurance_type"),
            
            "fetched_at": datetime.now().isoformat(),
            "note": "Limited insurance data available from SODA API. Use QCMobile API for complete insurance details."
        }
    
    def log(self, message: str, level: str = "INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)
        
        with open(self.log_file, 'a') as f:
            f.write(log_entry + "\n")
    
    def check_cache(self, usdot: int) -> Optional[Dict]:
        """Check if data exists in cache"""
        try:
            cache = json.loads(self.cache_file.read_text())
            return cache.get(str(usdot))
        except:
            return None
    
    def update_cache(self, usdot: int, data: Dict):
        """Update cache with new data"""
        try:
            cache = json.loads(self.cache_file.read_text())
            cache[str(usdot)] = data
            self.cache_file.write_text(json.dumps(cache, indent=2))
            self.log(f"Updated cache for USDOT {usdot}")
        except Exception as e:
            self.log(f"Cache update failed: {e}", "ERROR")
    
    def add_to_pending(self, usdot: int):
        """Add USDOT to pending queue"""
        try:
            pending = json.loads(self.pending_file.read_text())
            if usdot not in pending:
                pending.append(usdot)
                self.pending_file.write_text(json.dumps(pending, indent=2))
                self.log(f"Added {usdot} to pending queue")
        except Exception as e:
            self.log(f"Failed to add to pending: {e}", "ERROR")
    
    def get_insurance_data(self, usdot_number: int) -> Dict[str, Any]:
        """
        Get insurance data from available sources
        Tries QCMobile first (if key available), then falls back to SODA
        """
        # Check cache first
        cached = self.check_cache(usdot_number)
        if cached:
            self.log(f"Found cached data for {usdot_number}")
            return {
                "usdot_number": usdot_number,
                "success": True,
                "data": cached,
                "source": "cache"
            }
        
        result = {
            "usdot_number": usdot_number,
            "success": False,
            "data": None,
            "error": None
        }
        
        # Try QCMobile API first (most complete data)
        if self.webkey:
            print(f"Fetching from QCMobile API for USDOT {usdot_number}...")
            qc_data = self.get_carrier_from_qcmobile(usdot_number)
            if qc_data:
                result["success"] = True
                result["data"] = qc_data
                # Cache the result
                self.update_cache(usdot_number, qc_data)
                return result
        
        # Fall back to SODA API (no key required but limited data)
        print(f"Fetching from SODA Open Data API for USDOT {usdot_number}...")
        soda_data = self.get_carrier_from_soda(usdot_number)
        if soda_data:
            result["success"] = True
            result["data"] = soda_data
            # Cache the result
            self.update_cache(usdot_number, soda_data)
            return result
        
        # No data found - add to pending queue
        self.add_to_pending(usdot_number)
        result["error"] = "No insurance data found from available sources - added to pending queue"
        return result
    
    def get_pending_lookups(self) -> List[int]:
        """Get list of pending USDOT lookups"""
        try:
            return json.loads(self.pending_file.read_text())
        except:
            return []


def test_service():
    """Test the insurance service with known carriers"""
    
    # Initialize service
    service = FMCSAInsuranceService()
    
    # Test carriers (well-known companies)
    test_carriers = [
        {"usdot": 80321, "name": "FedEx"},
        {"usdot": 76830, "name": "UPS"},
        {"usdot": 65119, "name": "Schneider"},
        {"usdot": 62978, "name": "J.B. Hunt"},
        {"usdot": 31135, "name": "Swift Transportation"}
    ]
    
    print("=" * 80)
    print("FMCSA Insurance Data Service Test")
    print("=" * 80)
    
    if not service.webkey:
        print("\n⚠️  No FMCSA WebKey found. Using limited SODA API data.")
        print("   To get complete insurance data:")
        print("   1. Register at https://mobile.fmcsa.dot.gov/QCDevsite/")
        print("   2. Get your WebKey")
        print("   3. Set FMCSA_WEBKEY in .env file")
    else:
        print(f"\n✓ Using FMCSA WebKey: {service.webkey[:10]}...")
    
    print("\nTesting with known carriers:")
    print("-" * 80)
    
    for carrier_info in test_carriers[:2]:  # Test first 2
        usdot = carrier_info["usdot"]
        name = carrier_info["name"]
        
        print(f"\n{name} (USDOT: {usdot})")
        print("-" * 40)
        
        result = service.get_insurance_data(usdot)
        
        if result["success"]:
            data = result["data"]
            print(f"Source: {data.get('source')}")
            print(f"Legal Name: {data.get('legal_name')}")
            print(f"Operating Status: {data.get('operating_status')}")
            print(f"Power Units: {data.get('power_units')}")
            
            # Insurance details
            if data.get('source') == 'FMCSA QCMobile API':
                print("\nInsurance Information:")
                print(f"  Insurance Required: {data.get('insurance_required')}")
                print(f"  Insurance on File: {data.get('insurance_on_file')}")
                print(f"  BIPD Required: {data.get('bipd_required')}")
                print(f"  BIPD on File: {data.get('bipd_on_file')}")
                print(f"  Cargo Required: {data.get('cargo_required')}")
                print(f"  Cargo on File: {data.get('cargo_on_file')}")
                
                if data.get('insurance_carrier'):
                    print(f"  Insurance Carrier: {data.get('insurance_carrier')}")
                if data.get('policy_number'):
                    print(f"  Policy Number: {data.get('policy_number')}")
                if data.get('coverage_from'):
                    print(f"  Coverage From: {data.get('coverage_from')}")
                if data.get('coverage_to'):
                    print(f"  Coverage To: {data.get('coverage_to')}")
            else:
                print(f"\nNote: {data.get('note', 'Limited data available')}")
        else:
            print(f"Error: {result.get('error')}")
    
    print("\n" + "=" * 80)
    print("Test complete")
    

if __name__ == "__main__":
    test_service()