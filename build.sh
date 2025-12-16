#!/usr/bin/env bash
# Render build script for Chef Edwin

set -o errexit  # Exit on error

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Running database migrations..."
python manage.py migrate

echo "Creating superuser if needed..."
python create_superuser.py

echo "Build completed successfully!"
