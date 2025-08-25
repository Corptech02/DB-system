#!/bin/bash

# FMCSA System Startup Script
# This script sets up and runs the FMCSA Database Management System

set -e  # Exit on error

echo "========================================="
echo "FMCSA Database Management System"
echo "========================================="

# Check if running for the first time
FIRST_RUN=false
if [ ! -f ".env" ]; then
    FIRST_RUN=true
    echo "First time setup detected..."
fi

# Function to check if PostgreSQL is running
check_postgres() {
    if command -v pg_isready &> /dev/null; then
        pg_isready -q
        return $?
    else
        echo "Warning: pg_isready not found, assuming PostgreSQL is running"
        return 0
    fi
}

# Step 1: Environment Setup
if [ "$FIRST_RUN" = true ]; then
    echo ""
    echo "Step 1: Creating .env file..."
    cat > .env << 'EOF'
# Database
DATABASE_URL=postgresql://localhost:5432/fmcsa_db
DB_MIN_CONNECTIONS=5
DB_MAX_CONNECTIONS=20

# FMCSA API
FMCSA_API_URL=https://mobile.fmcsa.dot.gov/qc/services/carriers

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
ENABLE_CORS=true
CORS_ORIGINS=["http://localhost:3000"]

# Scheduler
ENABLE_SCHEDULER=false
REFRESH_SCHEDULE_HOUR=2
REFRESH_SCHEDULE_MINUTE=0

# Export Settings
EXPORT_MAX_ROWS_CSV=1000000
EXPORT_MAX_ROWS_EXCEL=1048576
EXPORT_CHUNK_SIZE=50000
EXPORT_TEMP_DIR=/tmp/fmcsa_exports

# Features
ENABLE_RATE_LIMITING=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=60
ENABLE_API_KEY_AUTH=false
EOF
    echo "✓ .env file created"
fi

# Step 2: Python Environment
echo ""
echo "Step 2: Setting up Python environment..."

if [ ! -d "venv_linux" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv_linux
fi

echo "Activating virtual environment..."
source venv_linux/bin/activate

echo "Installing Python dependencies..."
pip install -q -r fmcsa_system/requirements.txt
echo "✓ Python dependencies installed"

# Step 3: Database Setup
echo ""
echo "Step 3: Setting up PostgreSQL database..."

if ! check_postgres; then
    echo "PostgreSQL is not running. Please start PostgreSQL and run this script again."
    echo "On Ubuntu/Debian: sudo service postgresql start"
    echo "On MacOS: brew services start postgresql"
    exit 1
fi

# Check if database exists
if psql -lqt | cut -d \| -f 1 | grep -qw fmcsa_db; then
    echo "✓ Database 'fmcsa_db' already exists"
else
    echo "Creating database 'fmcsa_db'..."
    createdb fmcsa_db
    echo "✓ Database created"
    
    echo "Running database schema..."
    psql -d fmcsa_db -f fmcsa_system/database/schema.sql
    echo "✓ Schema created"
fi

# Step 4: Frontend Setup
echo ""
echo "Step 4: Setting up React dashboard..."

cd fmcsa_dashboard

if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
    echo "✓ Node dependencies installed"
else
    echo "✓ Node dependencies already installed"
fi

if [ ! -f ".env" ]; then
    echo "Creating frontend .env file..."
    cat > .env << 'EOF'
VITE_API_URL=http://localhost:8000/api
EOF
    echo "✓ Frontend .env created"
fi

cd ..

# Step 5: Start Services
echo ""
echo "========================================="
echo "Starting FMCSA System Services"
echo "========================================="
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down services..."
    kill $API_PID $FRONTEND_PID 2>/dev/null || true
    deactivate 2>/dev/null || true
    echo "Services stopped."
}

trap cleanup EXIT

# Start API server
echo "Starting API server on http://localhost:8000..."
uvicorn fmcsa_system.api.main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!

# Wait for API to start
sleep 5

# Start frontend
echo "Starting React dashboard on http://localhost:3000..."
cd fmcsa_dashboard
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "========================================="
echo "✓ FMCSA System is running!"
echo "========================================="
echo ""
echo "Services:"
echo "  • API Server: http://localhost:8000"
echo "  • API Docs: http://localhost:8000/docs"
echo "  • Dashboard: http://localhost:3000"
echo ""

if [ "$FIRST_RUN" = true ]; then
    echo "IMPORTANT: This is your first run!"
    echo ""
    echo "To load initial data (2.2M records, ~1-2 hours):"
    echo "  python -m fmcsa_system.ingestion.initial_load"
    echo ""
    echo "For a quick test with limited data (1000 records):"
    echo "  python -m fmcsa_system.ingestion.initial_load --limit 1000"
    echo ""
fi

echo "Press Ctrl+C to stop all services"
echo ""

# Wait for user to stop
wait $API_PID