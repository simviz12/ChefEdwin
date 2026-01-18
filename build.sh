#!/usr/bin/env bash
# Neon/Render build script for Chef Edwin

set -o errexit  # Exit on error

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Running database migrations..."
python manage.py migrate

echo "Creating/Updating admin user..."
python reset_chef.py


echo "Build completed successfully!"
