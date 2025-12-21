#!/bin/bash

echo "=== Starting Messenger App ==="

# Apply database migrations
echo "1. Applying database migrations..."
python manage.py migrate --no-input

# Collect static files
echo "2. Collecting static files..."
python manage.py collectstatic --no-input --clear

# Start Gunicorn server
echo "3. Starting Gunicorn server..."
exec gunicorn messenger_app.asgi:application \
    --bind 0.0.0.0:10000 \
    --workers 2 \
    --worker-class gthread \
    --threads 4 \
    --timeout 120 \
    --access-logfile -