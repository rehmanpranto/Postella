#!/usr/bin/env bash
# Render build script
set -o errexit

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Run database migrations if needed (creates tables)
python -c "from app import create_app; app = create_app('production'); print('✓ Build complete')"
