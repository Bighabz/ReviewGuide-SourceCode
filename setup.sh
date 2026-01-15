#!/bin/bash
#
# Quick database setup script for ReviewGuide
#
# Usage:
#   ./setup.sh              # Run migrations only
#   ./setup.sh --reset      # Drop database, recreate, run migrations, populate env configs, and create default admin user
#
# Prerequisites:
#   1. PostgreSQL running (brew services start postgresql)
#   2. Database created (createdb reviewguide_db)
#   3. backend/.env configured with DATABASE_URL
#
# Default admin user (created with --reset):
#   Username: admin
#   Password: admin123456
#   Email:    admin@reviewguide.ai
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=================================================="
echo "ReviewGuide Database Setup"
echo "=================================================="
echo ""

# Navigate to script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"

if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}❌ Backend directory not found${NC}"
    echo "Expected: $BACKEND_DIR"
    exit 1
fi

# Check for virtual environment
if [ -f "$SCRIPT_DIR/.venv/bin/python3.11" ]; then
    PYTHON_CMD="$SCRIPT_DIR/.venv/bin/python3.11"
    echo "Using virtual environment with Python 3.11"
elif [ -f "$SCRIPT_DIR/.venv/bin/python" ]; then
    PYTHON_CMD="$SCRIPT_DIR/.venv/bin/python"
    echo "Using virtual environment"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
    echo "Using system Python: $PYTHON_CMD"
else
    echo -e "${RED}❌ Python is not installed${NC}"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

echo ""

# Check if PostgreSQL is running
if ! pg_isready > /dev/null 2>&1; then
    echo -e "${RED}❌ PostgreSQL is not running${NC}"
    echo ""
    echo "Please start PostgreSQL first:"
    echo "  macOS:  brew services start postgresql"
    echo "  Linux:  sudo systemctl start postgresql"
    echo "  Docker: docker-compose up -d postgres"
    exit 1
fi

echo -e "${GREEN}✅ PostgreSQL is running${NC}"
echo ""

# Check if .env exists
if [ ! -f "$BACKEND_DIR/.env" ]; then
    echo -e "${RED}❌ .env file not found${NC}"
    echo ""
    echo "Please create .env from example:"
    echo "  cp backend/.env.example backend/.env"
    echo "  # Then edit backend/.env with your database credentials"
    exit 1
fi

echo -e "${GREEN}✅ .env file exists${NC}"
echo ""

# Change to backend directory
cd "$BACKEND_DIR"

# Parse arguments
if [ "$1" == "--reset" ]; then
    echo -e "${YELLOW}⚠️  Running in RESET mode (will delete existing data)${NC}"
    echo ""

    # Extract database name from .env
    DB_NAME=$(grep DATABASE_URL .env | cut -d'/' -f4 | cut -d'?' -f1)

    if [ -z "$DB_NAME" ]; then
        echo -e "${RED}❌ Could not parse database name from .env${NC}"
        exit 1
    fi

    echo "Dropping database: $DB_NAME (terminating all connections)"

    # Terminate all connections to the database first
    psql -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();" > /dev/null 2>&1 || true

    # Drop database if it exists
    dropdb --if-exists "$DB_NAME" 2>/dev/null

    # Create database
    echo "Creating database: $DB_NAME"
    createdb "$DB_NAME"

    echo -e "${GREEN}✅ Database reset complete${NC}"
    echo ""
fi

# Run Alembic migrations
echo "Running database migrations..."
echo ""

PYTHONPATH="$BACKEND_DIR" $PYTHON_CMD -m alembic upgrade head

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Database migrations complete!${NC}"
    echo ""

    # If --reset was used, populate env configs into database
    if [ "$1" == "--reset" ]; then
        echo "Populating core_config table with environment variables..."
        echo ""
        PYTHONPATH="$BACKEND_DIR" $PYTHON_CMD "$BACKEND_DIR/scripts/populate_env_configs.py"

        if [ $? -eq 0 ]; then
            echo ""
            echo -e "${GREEN}✅ Environment configs populated!${NC}"
        else
            echo ""
            echo -e "${YELLOW}⚠️  Failed to populate env configs (non-critical)${NC}"
        fi

        echo ""
        echo "Creating default admin user..."
        echo ""
        PYTHONPATH="$BACKEND_DIR" $PYTHON_CMD "$BACKEND_DIR/scripts/create_default_admin.py"

        if [ $? -eq 0 ]; then
            echo ""
            echo -e "${GREEN}✅ Default admin user created!${NC}"
        else
            echo ""
            echo -e "${YELLOW}⚠️  Failed to create default admin user (non-critical)${NC}"
        fi
    fi

    echo ""
    echo -e "${GREEN}✅ Database setup complete!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Start backend:  cd backend && $PYTHON_CMD -m uvicorn app.main:app --reload"
    echo "  2. Test query:     curl http://localhost:8000/health"
    echo ""
else
    echo ""
    echo -e "${RED}❌ Database setup failed${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check PostgreSQL is running: pg_isready"
    echo "  2. Check database exists: psql -l | grep reviewguide"
    echo "  3. Create database: createdb reviewguide_db"
    echo "  4. Check credentials in backend/.env"
    exit 1
fi
