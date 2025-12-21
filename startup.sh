#!/bin/bash
echo "=== Starting Messenger App ==="

# 1. Check project structure
echo "1. Checking project structure..."
ls -la

# 2. Set Python path
echo "2. Setting up Python paths..."
export PYTHONPATH="/opt/render/project/src:$PYTHONPATH"
echo "PYTHONPATH: $PYTHONPATH"

# 3. Check for manage.py
echo "3. Checking for manage.py..."
if [ -f "manage.py" ]; then
    echo "✓ Found manage.py"
else
    echo "✗ manage.py not found!"
    echo "Current directory: $(pwd)"
    ls -la
    exit 1
fi

# 4. Apply migrations
echo "4. Applying database migrations..."
python manage.py migrate --no-input

# 5. Collect static files
echo "5. Collecting static files..."
python manage.py collectstatic --no-input

# 6. Start server
echo "6. Starting Gunicorn server..."
exec gunicorn messenger.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --worker-class gthread \
    --threads 4 \
    --timeout 120 \
    --access-logfile -