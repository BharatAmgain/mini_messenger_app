#!/bin/bash
# startup.sh
echo "Running database migrations..."
python manage.py migrate --no-input

echo "Starting server..."
gunicorn messenger.wsgi:application