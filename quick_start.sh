#!/bin/bash

# AutoContent Calendar Quick Start Script
# This script helps you quickly set up and run the application

set -e

echo "🚀 AutoContent Calendar - Quick Start"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed. Please install Python 3.9 or higher.${NC}"
    exit 1
fi

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo -e "${YELLOW}⚠️  PostgreSQL is not installed or not in PATH.${NC}"
    echo "Please install PostgreSQL and try again."
    exit 1
fi

# Check if Redis is installed
if ! command -v redis-cli &> /dev/null; then
    echo -e "${YELLOW}⚠️  Redis is not installed or not in PATH.${NC}"
    echo "Please install Redis and try again."
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites check passed${NC}"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file from template..."
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please edit .env file with your configuration before continuing.${NC}"
    echo ""
    read -p "Press Enter when you've configured .env, or Ctrl+C to exit..."
fi

# Check if database exists
DB_NAME="autocontent_calendar"
if ! psql -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
    echo "🗄️  Creating database..."
    createdb $DB_NAME || {
        echo -e "${RED}❌ Failed to create database. You may need to do this manually.${NC}"
        exit 1
    }
    echo -e "${GREEN}✓ Database created${NC}"
fi

# Initialize database
echo "🗄️  Initializing database schema..."
flask init-db

echo -e "${GREEN}✓ Database initialized${NC}"
echo ""

# Create admin user
echo "👤 Creating admin user..."
echo "Please enter admin credentials:"
flask create-admin

echo ""
echo -e "${GREEN}✓ Admin user created${NC}"
echo ""

# Ask if user wants to generate sample data
read -p "Would you like to generate sample data for testing? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📊 Generating sample data..."
    python generate_sample_data.py
    echo ""
fi

# Check if Redis is running
if ! redis-cli ping &> /dev/null; then
    echo -e "${YELLOW}⚠️  Redis is not running. Starting Redis...${NC}"
    # Try to start Redis
    if command -v brew &> /dev/null; then
        brew services start redis
    else
        echo "Please start Redis manually in a separate terminal:"
        echo "  redis-server"
    fi
fi

echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "🎉 AutoContent Calendar is ready to run!"
echo ""
echo "To start the application, you need to run these commands in separate terminals:"
echo ""
echo -e "${YELLOW}Terminal 1 - Flask App:${NC}"
echo "  source venv/bin/activate && python app.py"
echo ""
echo -e "${YELLOW}Terminal 2 - Celery Worker:${NC}"
echo "  source venv/bin/activate && celery -A celery_worker.celery worker --loglevel=info"
echo ""
echo -e "${YELLOW}Terminal 3 - Celery Beat:${NC}"
echo "  source venv/bin/activate && celery -A celery_worker.celery beat --loglevel=info"
echo ""
echo "Or run them all in the background:"
echo "  ./run_all.sh"
echo ""
echo "Then open your browser to: http://localhost:5000/login.html"
echo ""
echo "Test credentials:"
echo "  Admin: admin@example.com / admin123"
echo "  Editor: editor@example.com / editor123"
echo ""
