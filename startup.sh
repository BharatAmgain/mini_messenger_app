#!/bin/bash
# startup.sh - Startup script for Render

echo "=== Starting Messenger App ==="

# Apply database migrations
echo "1. Applying database migrations..."
python manage.py migrate --no-input

# Collect static files
echo "2. Collecting static files..."
python manage.py collectstatic --no-input --clear

# Start Gunicorn server
echo "3. Starting Gunicorn server..."
exec gunicorn messenger.wsgi:application \
    --bind 0.0.0.0:10000 \
    --workers 2 \
    --threads 4 \
    --access-logfile - \
    --error-logfile - \
    --timeout 120