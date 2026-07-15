#!/bin/bash

echo "Setting up Aiva AI Bot..."

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Install dev dependencies
pip install -r requirements-dev.txt

# Create necessary directories
mkdir -p migrations/versions

# Initialize Alembic (if not already done)
if [ ! -f alembic.ini ]; then
    cp alembic.ini.example alembic.ini
fi

echo "Setup complete!"
echo "To activate the virtual environment, run: source venv/bin/activate"
echo "Or on Windows: venv\\Scripts\\activate"