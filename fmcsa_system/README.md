# FMCSA Database Management System

A high-performance system for ingesting and managing FMCSA (Federal Motor Carrier Safety Administration) carrier data with 2.2M+ USDOT records.

## Prerequisites

- Python 3.9+
- PostgreSQL 14+
- Node.js 18+ (for React dashboard)
- Redis (optional, for caching)

## Backend Setup

### 1. Install Python Dependencies

```bash
# Create virtual environment
python -m venv venv_linux
source venv_linux/bin/activate  # On Windows: venv_linux\Scripts\activate

# Install dependencies
pip install -r fmcsa_system/requirements.txt
```

### 2. PostgreSQL Database Setup

```bash
# Create database
createdb fmcsa_db

# Run schema
psql -d fmcsa_db -f fmcsa_system/database/schema.sql
```

### 3. Environment Configuration

Create a `.env` file in the project root:

```env
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/fmcsa_db
DB_MIN_CONNECTIONS=5
DB_MAX_CONNECTIONS=20

# FMCSA API
FMCSA_API_KEY=your_api_key_here  # Optional, for higher rate limits
FMCSA_API_URL=https://mobile.fmcsa.dot.gov/qc/services/carriers

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
ENABLE_CORS=true
CORS_ORIGINS=["http://localhost:3000"]

# Scheduler
ENABLE_SCHEDULER=true
REFRESH_SCHEDULE_HOUR=2  # 2 AM daily refresh
REFRESH_SCHEDULE_MINUTE=0
ENABLE_INCREMENTAL_UPDATES=false

# Export Settings
EXPORT_MAX_ROWS_CSV=1000000
EXPORT_MAX_ROWS_EXCEL=1048576
EXPORT_CHUNK_SIZE=50000
EXPORT_TEMP_DIR=/tmp/fmcsa_exports

# Optional Features
ENABLE_RATE_LIMITING=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=60
ENABLE_API_KEY_AUTH=false
API_KEYS=["key1", "key2"]  # If auth enabled
```

### 4. Initial Data Ingestion

```bash
# Run initial data load (this will take 1-2 hours for 2.2M records)
python -m fmcsa_system.ingestion.initial_load

# Or use the scheduler for automatic daily updates
python -m fmcsa_system.ingestion.scheduler
```

### 5. Start the API Server

```bash
# Development mode
uvicorn fmcsa_system.api.main:app --reload --host 0.0.0.0 --port 8000

# Production mode with multiple workers
gunicorn fmcsa_system.api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Frontend Setup

### 1. Install Node Dependencies

```bash
cd fmcsa_dashboard
npm install
```

### 2. Configure Environment

Create `fmcsa_dashboard/.env`:

```env
VITE_API_URL=http://localhost:8000/api
VITE_API_KEY=  # Optional, if API key auth is enabled
```

### 3. Start Development Server

```bash
npm run dev
# Dashboard will be available at http://localhost:3000
```

### 4. Build for Production

```bash
npm run build
# Output will be in fmcsa_dashboard/dist/
```

## Quick Start Guide

### Option 1: Docker Compose (Easiest)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: fmcsa_db
      POSTGRES_USER: fmcsa_user
      POSTGRES_PASSWORD: fmcsa_pass
    volumes:
      - ./fmcsa_system/database/schema.sql:/docker-entrypoint-initdb.d/01-schema.sql
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  api:
    build: .
    environment:
      DATABASE_URL: postgresql://fmcsa_user:fmcsa_pass@postgres:5432/fmcsa_db
      API_HOST: 0.0.0.0
      API_PORT: 8000
    ports:
      - "8000:8000"
    depends_on:
      - postgres
    command: uvicorn fmcsa_system.api.main:app --host 0.0.0.0 --port 8000

  frontend:
    build: ./fmcsa_dashboard
    ports:
      - "3000:3000"
    environment:
      VITE_API_URL: http://localhost:8000/api

volumes:
  postgres_data:
```

Then run:

```bash
docker-compose up
```

### Option 2: Manual Setup

```bash
# Terminal 1: Start PostgreSQL
sudo service postgresql start

# Terminal 2: Start API
source venv_linux/bin/activate
uvicorn fmcsa_system.api.main:app --reload

# Terminal 3: Start Frontend
cd fmcsa_dashboard
npm run dev

# Terminal 4: Run initial data load (one-time)
source venv_linux/bin/activate
python -m fmcsa_system.ingestion.initial_load
```

## API Endpoints

- **Search**: `POST /api/search` - Search carriers with filters
- **Carrier Details**: `GET /api/carriers/{usdot_number}` - Get specific carrier
- **Statistics**: `GET /api/stats` - Get aggregate statistics
- **Export**: `POST /api/export` - Export data to CSV/Excel
- **Leads**: `GET /api/leads/expiring-insurance` - Get insurance expiration leads
- **Admin**: `POST /api/admin/refresh` - Trigger manual data refresh

## Testing

```bash
# Run all tests
pytest

# Run specific test module
pytest tests/test_ingestion/

# Run with coverage
pytest --cov=fmcsa_system --cov-report=html
```

## Monitoring

The system includes built-in monitoring:

- API health check: `GET /api/health`
- Scheduler status: `GET /api/admin/scheduler-status`
- Database statistics: `GET /api/stats/summary`

## Performance Considerations

- Initial data load: ~1-2 hours for 2.2M records
- Daily refresh: ~30-45 minutes
- Search response: <100ms for most queries
- Export generation: ~1-2 minutes per 100k records

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
sudo service postgresql status

# Check connection
psql -U username -d fmcsa_db -c "SELECT 1;"
```

### Slow Ingestion

```bash
# Increase batch size in .env
INGESTION_BATCH_SIZE=10000

# Check API rate limits
curl -I https://mobile.fmcsa.dot.gov/qc/services/carriers/123456
```

### Memory Issues During Export

```bash
# Reduce chunk size in .env
EXPORT_CHUNK_SIZE=10000
```

## License

MIT