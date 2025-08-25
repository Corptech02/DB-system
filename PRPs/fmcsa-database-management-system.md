name: "FMCSA Database Management System PRP - Context-Rich with Validation Loops"
description: |

## Purpose
Build a comprehensive Database Management System for FMCSA Company Census File (USDOT dataset) with PostgreSQL backend, FastAPI REST API, and React dashboard for search, lead generation, compliance monitoring, and exports. This PRP provides complete context for one-pass implementation success.

## Core Principles
1. **Context is King**: All necessary FMCSA API documentation, PostgreSQL patterns, and FastAPI best practices included
2. **Validation Loops**: Executable tests and lints the AI can run and fix
3. **Information Dense**: Real patterns from codebase examples
4. **Progressive Success**: Start with database schema, then API, then ingestion
5. **Global rules**: Follow all rules in CLAUDE.md

---

## Goal
Build a production-ready database management system that:
- Automatically ingests and refreshes 2.2M+ USDOT records from FMCSA API
- Provides high-performance search and filtering capabilities
- Enables lead generation based on insurance expiration dates
- Supports bulk exports to CSV/Excel with chunked processing
- Includes a React dashboard for visual data exploration

IMPORTANT 
- Use the exsiting project in  Archon for the implementation
-Create the tass for the project and preform Archon Rag queries imediently after reading the PRP
## Why
- **Business value**: Enable trucking insurance agents to identify leads based on insurance expiration dates
- **Compliance monitoring**: Help companies track carrier compliance status
- **Market analysis**: Provide insights into carrier demographics and operations
- **Integration**: Foundation for future CRM and marketing automation integrations

## What
### User-visible behavior:
- Dashboard with search filters (USDOT#, state, carrier type, insurance expiration)
- Real-time results table with pagination
- Export functionality for filtered results
- Automated daily refresh of FMCSA data
- API endpoints for programmatic access

### Technical requirements:
- PostgreSQL with partitioning for 2.2M+ records
- Async FastAPI with connection pooling
- React + Tailwind CSS dashboard
- Pandas chunked processing for exports
- Scheduled ingestion via cron/APScheduler

### Success Criteria
- [ ] Complete ingestion of 2.2M+ FMCSA records
- [ ] Search queries return in <500ms for indexed fields
- [ ] Export of 100k records completes in <30 seconds
- [ ] Dashboard loads initial data in <2 seconds
- [ ] Daily automated refresh runs without manual intervention
- [ ] Insurance expiration calculations work correctly (30/60/90 days)

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- url: https://data.transportation.gov/resource/az4n-8mr2.json
  why: FMCSA Company Census API endpoint - primary data source
  
- url: https://dev.socrata.com/consumers/getting-started.html
  why: SODA API documentation for querying FMCSA data with pagination
  critical: Use $limit and $offset for pagination, max 50,000 records per page
  
- url: https://www.postgresql.org/docs/current/ddl-partitioning.html
  why: PostgreSQL partitioning guide for 2M+ record optimization
  section: Range partitioning by created_at for time-series data
  
- url: https://magicstack.github.io/asyncpg/current/usage.html
  why: asyncpg connection pooling patterns for FastAPI
  critical: Set max_inactive_connection_lifetime=300, min_size=5, max_size=20
  
- url: https://pandas.pydata.org/docs/user_guide/scale.html
  why: Pandas chunked processing for large CSV/Excel exports
  critical: Use chunksize=50000 for 2M+ row exports
  
- file: use-cases/agent-factory-with-subagents/agents/rag_agent/utils/db_utils.py
  why: DatabasePool pattern with asyncpg that we'll follow
  
- file: use-cases/agent-factory-with-subagents/agents/rag_agent/ingestion/ingest.py
  why: Ingestion pipeline pattern with progress callbacks
  
- file: use-cases/agent-factory-with-subagents/agents/rag_agent/sql/schema.sql
  why: PostgreSQL schema patterns with indexes and functions

- docfile: INITIAL.md
  why: Original feature requirements and examples
```

### Current Codebase tree
```bash
/mnt/d/context-engineering-intro/
├── CLAUDE.md
├── INITIAL.md
├── PRPs/
│   ├── templates/
│   │   └── prp_base.md
│   └── fmcsa-database-management-system.md (this file)
├── examples/
└── use-cases/
```

### Desired Codebase tree with files to be added
```bash
/mnt/d/context-engineering-intro/
├── fmcsa_system/
│   ├── __init__.py
│   ├── requirements.txt              # All Python dependencies
│   ├── .env.example                   # Environment template
│   ├── README.md                      # Setup and usage documentation
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── schema.sql                 # PostgreSQL schema with partitioning
│   │   ├── migrations/                # Alembic migrations
│   │   │   └── 001_initial_schema.sql
│   │   └── connection.py              # AsyncPG connection pool
│   │
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── fmcsa_client.py           # SODA API client for FMCSA
│   │   ├── ingestion_pipeline.py     # Main ingestion logic
│   │   ├── scheduler.py              # APScheduler for daily refresh
│   │   └── data_cleaner.py           # Data validation and normalization
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI app initialization
│   │   ├── models.py                 # Pydantic models
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── search.py             # Search endpoints
│   │   │   ├── export.py             # Export endpoints
│   │   │   └── stats.py              # Statistics endpoints
│   │   ├── dependencies.py           # Dependency injection
│   │   └── middleware.py             # CORS, auth middleware
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── search_service.py         # Search business logic
│   │   ├── export_service.py         # Export with Pandas chunking
│   │   ├── lead_generator.py         # Insurance expiration logic
│   │   └── cache_service.py          # Redis caching (optional)
│   │
│   ├── dashboard/                    # React frontend
│   │   ├── package.json
│   │   ├── src/
│   │   │   ├── App.jsx
│   │   │   ├── components/
│   │   │   │   ├── SearchForm.jsx
│   │   │   │   ├── ResultsTable.jsx
│   │   │   │   └── ExportButton.jsx
│   │   │   └── api/
│   │   │       └── client.js         # API client
│   │   └── tailwind.config.js
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py               # Pytest fixtures
│   │   ├── test_ingestion.py
│   │   ├── test_api.py
│   │   ├── test_search.py
│   │   └── test_export.py
│   │
│   └── examples/
│       ├── import_script.py          # Standalone ingestion example
│       ├── query_examples.sql        # Common SQL queries
│       ├── dashboard_demo.py         # API integration demo
│       └── export_to_csv.py          # Export example
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: FMCSA SODA API limits
# - Max 50,000 records per request (use $limit and $offset)
# - Rate limiting: No official limit but be respectful (add delays)
# - Use application token to avoid shared pool cutoff
# Example: ?$limit=50000&$offset=100000

# CRITICAL: PostgreSQL partitioning for 2.2M rows
# - Partition by created_at for time-series (daily partitions recommended)
# - Cannot have unique constraints across partitions
# - Use pg_partman for automated partition management
# - Indexes on partitioned tables only cover subset of data

# CRITICAL: AsyncPG connection pooling in FastAPI
# - Don't share connections, share the pool
# - Use max_inactive_connection_lifetime=300 (5 minutes)
# - Add pool to request.state in middleware
# - Always use async with pool.acquire() as conn:

# CRITICAL: Pandas memory optimization for 2M+ rows
# - Use chunksize=50000 when reading/writing CSV
# - Excel has 1,048,576 row limit - provide CSV for full exports
# - Use dtype optimization to reduce memory usage
# - Consider Dask for datasets >1GB

# CRITICAL: React + FastAPI CORS
# - Must configure CORS middleware in FastAPI
# - Allow origins for localhost:3000 (React dev server)
# - Include credentials for auth cookies if needed
```

## Implementation Blueprint

### Data models and structure

```python
# PostgreSQL Schema with partitioning
"""
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- For text search
CREATE EXTENSION IF NOT EXISTS btree_gin; -- For compound indexes

-- Main carriers table (partitioned by created_at)
CREATE TABLE carriers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usdot_number INTEGER UNIQUE NOT NULL,
    legal_name TEXT NOT NULL,
    dba_name TEXT,
    
    -- Address information
    physical_address TEXT,
    physical_city TEXT,
    physical_state VARCHAR(2),
    physical_zip VARCHAR(10),
    physical_country VARCHAR(2),
    
    mailing_address TEXT,
    mailing_city TEXT,
    mailing_state VARCHAR(2),
    mailing_zip VARCHAR(10),
    
    -- Contact information
    telephone VARCHAR(20),
    fax VARCHAR(20),
    email TEXT,
    
    -- Carrier details
    mcs_150_date DATE,
    mcs_150_mileage INTEGER,
    entity_type VARCHAR(50),
    operating_status VARCHAR(50),
    out_of_service_date DATE,
    
    -- Operations
    power_units INTEGER,
    drivers INTEGER,
    carrier_operation VARCHAR(100),
    cargo_carried TEXT[],
    
    -- Insurance
    liability_insurance_date DATE,
    liability_insurance_amount DECIMAL(12,2),
    cargo_insurance_date DATE,
    cargo_insurance_amount DECIMAL(12,2),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    raw_data JSONB  -- Store complete FMCSA record
) PARTITION BY RANGE (created_at);

-- Create indexes on partition parent
CREATE INDEX idx_carriers_usdot ON carriers(usdot_number);
CREATE INDEX idx_carriers_state ON carriers(physical_state);
CREATE INDEX idx_carriers_entity_type ON carriers(entity_type);
CREATE INDEX idx_carriers_operating_status ON carriers(operating_status);
CREATE INDEX idx_carriers_insurance_exp ON carriers(liability_insurance_date);
CREATE INDEX idx_carriers_legal_name_trgm ON carriers USING gin(legal_name gin_trgm_ops);

-- Function for insurance expiration calculations
CREATE OR REPLACE FUNCTION get_insurance_expiring(days_ahead INTEGER)
RETURNS TABLE (
    usdot_number INTEGER,
    legal_name TEXT,
    liability_insurance_date DATE,
    days_until_expiration INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.usdot_number,
        c.legal_name,
        c.liability_insurance_date,
        (c.liability_insurance_date - CURRENT_DATE)::INTEGER as days_until_expiration
    FROM carriers c
    WHERE c.liability_insurance_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '1 day' * days_ahead
    AND c.operating_status = 'ACTIVE'
    ORDER BY c.liability_insurance_date;
END;
$$ LANGUAGE plpgsql;
"""

# Pydantic models
from pydantic import BaseModel, Field, ConfigDict
from datetime import date, datetime
from typing import Optional, List
from decimal import Decimal
from uuid import UUID

class CarrierBase(BaseModel):
    """Base carrier model with FMCSA fields"""
    model_config = ConfigDict(from_attributes=True)
    
    usdot_number: int = Field(..., description="USDOT Number")
    legal_name: str = Field(..., max_length=255)
    dba_name: Optional[str] = None
    
    physical_address: Optional[str] = None
    physical_city: Optional[str] = None
    physical_state: Optional[str] = Field(None, max_length=2)
    physical_zip: Optional[str] = Field(None, max_length=10)
    
    entity_type: Optional[str] = None
    operating_status: Optional[str] = None
    
    power_units: Optional[int] = None
    drivers: Optional[int] = None
    
    liability_insurance_date: Optional[date] = None
    liability_insurance_amount: Optional[Decimal] = None

class CarrierCreate(CarrierBase):
    """Model for creating carrier from FMCSA data"""
    raw_data: dict  # Complete FMCSA record

class CarrierResponse(CarrierBase):
    """Response model with calculated fields"""
    id: UUID
    days_until_insurance_expiration: Optional[int] = None
    insurance_status: Optional[str] = None  # "expired", "expiring_soon", "valid"
    
    @property
    def insurance_status(self) -> Optional[str]:
        if not self.liability_insurance_date:
            return None
        days = (self.liability_insurance_date - date.today()).days
        if days < 0:
            return "expired"
        elif days <= 30:
            return "expiring_soon"
        return "valid"

class SearchFilters(BaseModel):
    """Search query parameters"""
    usdot_number: Optional[int] = None
    state: Optional[str] = Field(None, max_length=2)
    entity_type: Optional[str] = None
    operating_status: Optional[str] = None
    insurance_expiring_days: Optional[int] = Field(None, ge=0, le=365)
    
    # Pagination
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)

class ExportRequest(BaseModel):
    """Export request parameters"""
    filters: SearchFilters
    format: str = Field("csv", pattern="^(csv|xlsx)$")
    columns: Optional[List[str]] = None
```

### List of tasks to be completed in order

```yaml
Task 1: Database Setup and Schema Creation
CREATE database/schema.sql:
  - Define partitioned carriers table
  - Create necessary indexes for performance
  - Add insurance expiration calculation functions
  - Setup trigger for updated_at timestamp

CREATE database/connection.py:
  - MIRROR pattern from: use-cases/agent-factory-with-subagents/agents/rag_agent/utils/db_utils.py
  - Implement DatabasePool class with asyncpg
  - Configure connection pooling (min=5, max=20)
  - Add connection health check

Task 2: FMCSA API Client Implementation
CREATE ingestion/fmcsa_client.py:
  - Implement SODA API client with pagination support
  - Handle $limit=50000 and $offset parameters
  - Add retry logic with exponential backoff
  - Include progress tracking callbacks

Task 3: Data Ingestion Pipeline
CREATE ingestion/ingestion_pipeline.py:
  - PATTERN from: use-cases/agent-factory-with-subagents/agents/rag_agent/ingestion/ingest.py
  - Process FMCSA data in batches
  - Normalize and validate carrier data
  - Handle upserts (INSERT ... ON CONFLICT)
  - Track ingestion metrics

Task 4: FastAPI Application Setup
CREATE api/main.py:
  - Initialize FastAPI app with lifespan events
  - Setup CORS middleware for React frontend
  - Add database pool to app.state
  - Configure exception handlers

CREATE api/dependencies.py:
  - Database connection dependency
  - Pagination parameters dependency
  - Authentication dependency (if needed)

Task 5: Search and Filter Endpoints
CREATE api/routes/search.py:
  - GET /api/carriers - List carriers with filters
  - GET /api/carriers/{usdot_number} - Get single carrier
  - GET /api/carriers/expiring - Insurance expiring soon
  - Use asyncpg prepared statements for performance

Task 6: Export Service with Chunking
CREATE services/export_service.py:
  - Implement chunked CSV export (50k rows per chunk)
  - Handle Excel export with 1M row limit warning
  - Stream response to avoid memory issues
  - Add progress tracking for large exports

Task 7: Lead Generation Service
CREATE services/lead_generator.py:
  - Calculate insurance expiration windows (30/60/90 days)
  - Score leads based on criteria
  - Generate contact lists for outreach
  - Export to CRM-compatible format

Task 8: Scheduled Data Refresh
CREATE ingestion/scheduler.py:
  - Setup APScheduler for daily refresh
  - Implement incremental updates (modified since last run)
  - Add failure notifications
  - Log refresh metrics

Task 9: React Dashboard
CREATE dashboard/src/App.jsx:
  - Main application layout with Tailwind CSS
  - State management for filters and results
  - API client configuration

CREATE dashboard/src/components/SearchForm.jsx:
  - Filter inputs (USDOT, state, entity type, etc.)
  - Insurance expiration date picker
  - Submit and reset functionality

CREATE dashboard/src/components/ResultsTable.jsx:
  - Paginated data table
  - Sortable columns
  - Row selection for export
  - Insurance status indicators

Task 10: Testing Suite
CREATE tests/test_ingestion.py:
  - Test FMCSA API pagination
  - Test data validation and normalization
  - Test database upserts

CREATE tests/test_api.py:
  - Test search endpoints with various filters
  - Test pagination
  - Test export functionality
  - Test error handling

Task 11: Examples and Documentation
CREATE examples/import_script.py:
  - Standalone script to import FMCSA data
  - Show pagination handling
  - Include progress bar

CREATE examples/query_examples.sql:
  - Common search queries
  - Insurance expiration queries
  - Performance analysis queries

CREATE README.md:
  - Setup instructions
  - Environment variables documentation
  - API endpoint documentation
  - Dashboard usage guide
```

### Per task pseudocode

```python
# Task 2: FMCSA API Client
async def fetch_fmcsa_data(offset: int = 0, limit: int = 50000) -> dict:
    """
    Fetch FMCSA data with pagination.
    CRITICAL: SODA API returns max 50,000 records per request
    """
    # PATTERN: Use httpx for async requests
    async with httpx.AsyncClient() as client:
        # GOTCHA: Must include application token to avoid rate limits
        headers = {"X-App-Token": os.getenv("SODA_APP_TOKEN")}
        
        # Build query with pagination
        params = {
            "$limit": limit,
            "$offset": offset,
            "$order": "usdot_number"  # Consistent ordering for pagination
        }
        
        # CRITICAL: Base URL without .json for query parameters
        url = "https://data.transportation.gov/resource/az4n-8mr2.json"
        
        # Retry logic for transient failures
        @retry(attempts=3, delay=1, backoff=2)
        async def _fetch():
            response = await client.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        
        return await _fetch()

# Task 3: Ingestion Pipeline
async def ingest_carriers(progress_callback=None) -> dict:
    """
    Ingest all FMCSA carriers with progress tracking.
    PATTERN: Similar to rag_agent/ingestion/ingest.py
    """
    total_processed = 0
    batch_size = 50000
    
    async with db_pool.acquire() as conn:
        while True:
            # Fetch batch from API
            data = await fetch_fmcsa_data(offset=total_processed, limit=batch_size)
            
            if not data:
                break  # No more records
            
            # PATTERN: Bulk upsert using asyncpg copy_records_to_table
            records = []
            for record in data:
                # CRITICAL: Normalize field names from FMCSA to our schema
                carrier = normalize_fmcsa_record(record)
                records.append(carrier)
            
            # GOTCHA: Use COPY for performance with large batches
            await conn.copy_records_to_table(
                'carriers',
                records=records,
                columns=['usdot_number', 'legal_name', ...],
                on_conflict='(usdot_number) DO UPDATE SET updated_at = CURRENT_TIMESTAMP'
            )
            
            total_processed += len(data)
            
            if progress_callback:
                progress_callback(total_processed, estimated_total=2200000)
            
            # Be respectful to API
            await asyncio.sleep(0.5)
    
    return {"total_processed": total_processed}

# Task 5: Search Implementation
async def search_carriers(filters: SearchFilters) -> List[CarrierResponse]:
    """
    Search carriers with filters and pagination.
    PATTERN: Use asyncpg prepared statements for performance
    """
    async with db_pool.acquire() as conn:
        # Build dynamic query based on filters
        query = """
            SELECT * FROM carriers c
            WHERE 1=1
        """
        params = []
        param_count = 0
        
        if filters.usdot_number:
            param_count += 1
            query += f" AND c.usdot_number = ${param_count}"
            params.append(filters.usdot_number)
        
        if filters.state:
            param_count += 1
            query += f" AND c.physical_state = ${param_count}"
            params.append(filters.state)
        
        if filters.insurance_expiring_days:
            # CRITICAL: Use the function we created in schema
            param_count += 1
            query += f"""
                AND c.liability_insurance_date BETWEEN CURRENT_DATE 
                AND CURRENT_DATE + INTERVAL '1 day' * ${param_count}
            """
            params.append(filters.insurance_expiring_days)
        
        # Add pagination
        query += f" LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
        params.extend([filters.limit, filters.offset])
        
        # PATTERN: Use prepared statement for repeated queries
        stmt = await conn.prepare(query)
        rows = await stmt.fetch(*params)
        
        return [CarrierResponse(**dict(row)) for row in rows]

# Task 6: Export Service
async def export_carriers_chunked(filters: SearchFilters, format: str):
    """
    Export carriers with chunked processing for memory efficiency.
    CRITICAL: Use pandas chunksize for 2M+ rows
    """
    chunk_size = 50000  # Optimal for memory usage
    
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f'.{format}')
    
    try:
        # Initialize writer based on format
        if format == 'csv':
            writer = None  # Will initialize on first chunk
        else:  # xlsx
            writer = pd.ExcelWriter(temp_file.name, engine='xlsxwriter')
        
        offset = 0
        chunk_num = 0
        
        while True:
            # Fetch chunk from database
            filters.limit = chunk_size
            filters.offset = offset
            
            carriers = await search_carriers(filters)
            
            if not carriers:
                break  # No more data
            
            # Convert to DataFrame
            df = pd.DataFrame([c.dict() for c in carriers])
            
            # GOTCHA: Excel has 1,048,576 row limit
            if format == 'xlsx' and offset + len(df) > 1048576:
                logger.warning("Excel row limit reached, truncating export")
                df = df.iloc[:1048576 - offset]
                
            # Write chunk
            if format == 'csv':
                # Append mode for CSV
                df.to_csv(temp_file.name, mode='a', header=(chunk_num == 0), index=False)
            else:
                # For Excel, accumulate in writer
                df.to_excel(writer, sheet_name='Carriers', startrow=offset, header=(chunk_num == 0), index=False)
            
            offset += chunk_size
            chunk_num += 1
            
            # CRITICAL: Check if we should stop for Excel
            if format == 'xlsx' and offset >= 1048576:
                break
        
        if format == 'xlsx':
            writer.close()
        
        return temp_file.name
        
    except Exception as e:
        os.unlink(temp_file.name)
        raise
```

### Integration Points
```yaml
DATABASE:
  - migration: "Create partitioned carriers table with insurance functions"
  - index: "CREATE INDEX idx_carriers_insurance_exp ON carriers(liability_insurance_date)"
  - partition: "CREATE TABLE carriers_2024_01 PARTITION OF carriers FOR VALUES FROM ('2024-01-01') TO ('2024-02-01')"
  
CONFIG:
  - add to: .env.example
  - pattern: |
      DATABASE_URL=postgresql://user:pass@localhost/fmcsa_db
      SODA_APP_TOKEN=your_token_here
      REDIS_URL=redis://localhost:6379 (optional)
      REACT_APP_API_URL=http://localhost:8000
  
ROUTES:
  - add to: api/main.py
  - pattern: |
      from api.routes import search, export, stats
      app.include_router(search.router, prefix="/api")
      app.include_router(export.router, prefix="/api")
      app.include_router(stats.router, prefix="/api")

MIDDLEWARE:
  - add to: api/main.py
  - pattern: |
      from fastapi.middleware.cors import CORSMiddleware
      app.add_middleware(
          CORSMiddleware,
          allow_origins=["http://localhost:3000"],  # React dev server
          allow_credentials=True,
          allow_methods=["*"],
          allow_headers=["*"],
      )

SCHEDULER:
  - add to: ingestion/scheduler.py
  - pattern: |
      from apscheduler.schedulers.asyncio import AsyncIOScheduler
      scheduler = AsyncIOScheduler()
      scheduler.add_job(ingest_carriers, 'cron', hour=2, minute=0)  # 2 AM daily
      scheduler.start()
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Run these FIRST - fix any errors before proceeding
ruff check fmcsa_system/ --fix      # Auto-fix Python issues
mypy fmcsa_system/                  # Type checking
black fmcsa_system/                  # Format code

# Expected: No errors. If errors, READ the error and fix.
```

### Level 2: Unit Tests
```python
# CREATE test_ingestion.py with these test cases:
import pytest
from unittest.mock import AsyncMock, patch
from ingestion.fmcsa_client import fetch_fmcsa_data

@pytest.mark.asyncio
async def test_fetch_with_pagination():
    """Test FMCSA API pagination works correctly"""
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_get.return_value.json = AsyncMock(return_value=[{"usdot_number": 123}])
        
        result = await fetch_fmcsa_data(offset=100000, limit=50000)
        
        # Verify pagination parameters
        call_args = mock_get.call_args[1]
        assert call_args['params']['$offset'] == 100000
        assert call_args['params']['$limit'] == 50000

@pytest.mark.asyncio  
async def test_insurance_expiration_calculation():
    """Test insurance expiration date calculations"""
    from datetime import date, timedelta
    from services.lead_generator import calculate_expiration_status
    
    # Test expired
    expired_date = date.today() - timedelta(days=10)
    assert calculate_expiration_status(expired_date) == "expired"
    
    # Test expiring soon (within 30 days)
    expiring_date = date.today() + timedelta(days=15)
    assert calculate_expiration_status(expiring_date) == "expiring_soon"
    
    # Test valid
    valid_date = date.today() + timedelta(days=60)
    assert calculate_expiration_status(valid_date) == "valid"

@pytest.mark.asyncio
async def test_chunked_export():
    """Test export handles large datasets correctly"""
    from services.export_service import export_carriers_chunked
    
    # Mock search to return 150k records in chunks
    with patch('services.export_service.search_carriers') as mock_search:
        # Simulate 3 chunks of 50k each
        mock_search.side_effect = [
            [{"usdot_number": i} for i in range(50000)],
            [{"usdot_number": i} for i in range(50000, 100000)],
            [{"usdot_number": i} for i in range(100000, 150000)],
            []  # Empty to stop iteration
        ]
        
        filepath = await export_carriers_chunked(SearchFilters(), "csv")
        
        # Verify file was created and has correct row count
        import pandas as pd
        df = pd.read_csv(filepath)
        assert len(df) == 150000
```

```bash
# Run tests and iterate until passing:
pytest fmcsa_system/tests/ -v --asyncio-mode=auto

# If failing: Read error, understand root cause, fix code, re-run
```

### Level 3: Database Integration Test
```bash
# Create test database
createdb fmcsa_test

# Run schema migration
psql fmcsa_test < fmcsa_system/database/schema.sql

# Test database operations
python -m pytest fmcsa_system/tests/test_database.py -v

# Expected: All database operations work with partitioning
```

### Level 4: API Integration Test
```bash
# Start the FastAPI service
cd fmcsa_system
uvicorn api.main:app --reload --port 8000

# Test search endpoint
curl -X GET "http://localhost:8000/api/carriers?state=CA&limit=10"

# Test export endpoint
curl -X POST "http://localhost:8000/api/export" \
  -H "Content-Type: application/json" \
  -d '{"filters": {"state": "TX"}, "format": "csv"}'

# Expected: JSON responses with carrier data
# If error: Check logs at logs/app.log for stack trace
```

### Level 5: Full Ingestion Test
```bash
# Run ingestion for small sample (first 10k records)
python fmcsa_system/examples/import_script.py --limit 10000

# Verify data in database
psql fmcsa_db -c "SELECT COUNT(*) FROM carriers;"

# Expected: 10000 rows imported
```

### Level 6: Dashboard Test
```bash
# Install dashboard dependencies
cd fmcsa_system/dashboard
npm install

# Start React development server
npm start

# Open browser to http://localhost:3000
# Test: Search form, results table, export button

# Expected: Dashboard loads, can search and view results
```

## Final Validation Checklist
- [ ] All tests pass: `pytest fmcsa_system/tests/ -v`
- [ ] No linting errors: `ruff check fmcsa_system/`
- [ ] No type errors: `mypy fmcsa_system/`
- [ ] Database migrations run successfully
- [ ] Can ingest 10k records without errors
- [ ] API returns results in <500ms for indexed queries
- [ ] Export of 100k records completes successfully
- [ ] Dashboard displays data correctly
- [ ] Scheduled refresh runs at 2 AM
- [ ] Insurance expiration calculations are accurate
- [ ] Documentation complete in README.md

---

## Anti-Patterns to Avoid
- ❌ Don't fetch all 2.2M records at once - use pagination
- ❌ Don't skip database indexing - queries will be too slow
- ❌ Don't use synchronous database drivers with FastAPI
- ❌ Don't load entire export into memory - use chunking
- ❌ Don't hardcode API tokens - use environment variables
- ❌ Don't ignore FMCSA rate limits - add delays
- ❌ Don't create unique constraints across partitions
- ❌ Don't export >1M rows to Excel - use CSV instead
- ❌ Don't share database connections - share the pool
- ❌ Don't skip data validation - FMCSA data can be inconsistent

## Performance Optimization Tips
- Use database partitioning for time-series data (daily/monthly)
- Implement Redis caching for frequently accessed carriers
- Use PostgreSQL materialized views for dashboard statistics
- Enable query result caching in React with React Query
- Use database connection pooling with min=5, max=20
- Index all columns used in WHERE clauses
- Use COPY instead of INSERT for bulk data loading
- Stream large exports instead of loading into memory

## Security Considerations
- Store SODA API token securely in environment variables
- Implement rate limiting on API endpoints
- Add authentication for dashboard access (JWT/OAuth)
- Validate and sanitize all user inputs
- Use parameterized queries to prevent SQL injection
- Enable HTTPS for production deployment
- Implement audit logging for data access
- Regular backups of PostgreSQL database

---

## Quality Score: 9/10

**Confidence for one-pass implementation: HIGH**

This PRP includes:
- ✅ Complete API documentation and gotchas
- ✅ Real code patterns from existing codebase
- ✅ Detailed schema with partitioning strategy
- ✅ Comprehensive validation loops
- ✅ Memory optimization strategies for 2M+ records
- ✅ All critical library quirks documented
- ✅ Step-by-step implementation tasks
- ✅ Complete test cases and validation steps
- ✅ Performance optimization guidelines

The AI agent has everything needed to successfully implement this FMCSA Database Management System in one pass.