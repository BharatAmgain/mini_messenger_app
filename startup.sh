#!/bin/bash
# startup.sh - Run migrations and start server
echo "=== Starting Messenger App ==="
echo "1. Applying database migrations..."
python manage.py migrate --no-input

echo "2. Collecting static files..."
python manage.py collectstatic --noinput

echo "3. Starting Gunicorn server..."
exec gunicorn messenger.wsgi:application