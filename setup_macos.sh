#!/bin/bash

# AutoContent Calendar - macOS Setup Script
# This script will install all prerequisites and set up the application

set -e

echo "=========================================="
echo "AutoContent Calendar - macOS Setup"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Homebrew is installed
echo "Checking Homebrew..."
if ! command -v brew &> /dev/null; then
    echo -e "${YELLOW}Homebrew not found. Installing...${NC}"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo -e "${GREEN}✓ Homebrew found${NC}"
fi

# Install PostgreSQL
echo ""
echo "Checking PostgreSQL..."
if ! command -v psql &> /dev/null; then
    echo -e "${YELLOW}Installing PostgreSQL...${NC}"
    brew install postgresql@14
    brew services start postgresql@14
    # Add to PATH
    echo 'export PATH="/opt/homebrew/opt/postgresql@14/bin:$PATH"' >> ~/.zshrc
    export PATH="/opt/homebrew/opt/postgresql@14/bin:$PATH"
else
    echo -e "${GREEN}✓ PostgreSQL found${NC}"
    # Make sure it's running
    brew services start postgresql@14 2>/dev/null || brew services restart postgresql@14 2>/dev/null || true
fi

# Install Redis
echo ""
echo "Checking Redis..."
if ! command -v redis-server &> /dev/null; then
    echo -e "${YELLOW}Installing Redis...${NC}"
    brew install redis
    brew services start redis
else
    echo -e "${GREEN}✓ Redis found${NC}"
    # Make sure it's running
    brew services start redis 2>/dev/null || brew services restart redis 2>/dev/null || true
fi

# Wait a moment for services to start
sleep 2

# Create Python virtual environment
echo ""
echo "Setting up Python environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment exists${NC}"
fi

# Activate virtual environment and install dependencies
source venv/bin/activate
echo ""
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file
echo ""
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    
    # Generate random secret keys
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    
    # Update .env file with generated keys
    sed -i '' "s|SECRET_KEY=your-secret-key-here|SECRET_KEY=$SECRET_KEY|g" .env
    sed -i '' "s|JWT_SECRET_KEY=your-jwt-secret-key-here|JWT_SECRET_KEY=$JWT_SECRET_KEY|g" .env
    sed -i '' "s|ENCRYPTION_KEY=your-encryption-key-here|ENCRYPTION_KEY=$ENCRYPTION_KEY|g" .env
    
    echo -e "${GREEN}✓ .env file created with secure keys${NC}"
else
    echo -e "${GREEN}✓ .env file exists${NC}"
fi

# Create database
echo ""
echo "Setting up database..."
DB_EXISTS=$(psql -U $(whoami) -lqt | cut -d \| -f 1 | grep -w autocontent_calendar | wc -l)
if [ $DB_EXISTS -eq 0 ]; then
    createdb autocontent_calendar
    echo -e "${GREEN}✓ Database created${NC}"
else
    echo -e "${GREEN}✓ Database exists${NC}"
fi

# Update DATABASE_URL in .env to use correct username
CURRENT_USER=$(whoami)
sed -i '' "s|postgresql://postgres:postgres@localhost/autocontent_calendar|postgresql://$CURRENT_USER@localhost/autocontent_calendar|g" .env

# Initialize database
echo ""
echo "Initializing database schema..."
flask init-db

# Create admin user
echo ""
echo "Creating admin user..."
echo ""
echo -e "${YELLOW}Please enter admin details:${NC}"
flask create-admin

# Create necessary directories
mkdir -p uploads logs

echo ""
echo -e "${GREEN}=========================================="
echo "✓ Setup Complete!"
echo "==========================================${NC}"
echo ""
echo "To start the application:"
echo "  1. Start all services: ./run_all.sh"
echo "  2. Open browser: http://localhost:5000/login.html"
echo ""
echo "To generate sample data (optional):"
echo "  python generate_sample_data.py"
echo ""
echo "To stop the application:"
echo "  ./stop_all.sh"
echo ""
echo -e "${YELLOW}Note: PostgreSQL and Redis are running as background services.${NC}"
echo ""
