#!/bin/bash

echo "=== Starting Messenger App ==="

# Debug: Show current directory structure
echo "1. Checking project structure..."
pwd
ls -la

# Fix Python paths and project structure
echo "2. Setting up Python paths..."
# Add current directory to Python path
CURRENT_DIR=$(pwd)
export PYTHONPATH="$CURRENT_DIR:$PYTHONPATH"
echo "PYTHONPATH: $PYTHONPATH"

# Check if we're in messenger_app directory
if [ -d "messenger_app" ]; then
    echo "3. Found messenger_app directory, adjusting paths..."
    cd messenger_app
    export PYTHONPATH="$(pwd):$PYTHONPATH"
    echo "Changed to: $(pwd)"
    echo "PYTHONPATH: $PYTHONPATH"
fi

# Debug: Check if manage.py exists
echo "4. Checking for manage.py..."
if [ -f "manage.py" ]; then
    echo "✓ Found manage.py"
else
    echo "✗ ERROR: manage.py not found in $(pwd)"
    echo "Listing files:"
    ls -la
    exit 1
fi

# Debug: Check Python and Django
echo "5. Checking Python and Django..."
python --version
python -c "import django; print(f'Django version: {django.__version__}')"

# Apply database migrations
echo "6. Applying database migrations..."
python manage.py migrate --no-input
if [ $? -eq 0 ]; then
    echo "✓ Migrations completed successfully"
else
    echo "✗ Migrations failed"
    exit 1
fi

# Collect static files
echo "7. Collecting static files..."
python manage.py collectstatic --no-input --clear
if [ $? -eq 0 ]; then
    echo "✓ Static files collected successfully"
else
    echo "✗ Static file collection failed"
    exit 1
fi

# Check for Gunicorn
echo "8. Checking Gunicorn..."
python -c "import gunicorn; print(f'Gunicorn available')"

# Start Gunicorn server with explicit module path
echo "9. Starting Gunicorn server..."
echo "Starting command: gunicorn messenger.asgi:application --bind 0.0.0.0:10000 --workers 2 --worker-class gthread --threads 4 --timeout 120 --access-logfile -"

# Try different module paths if needed
if python -c "import messenger" 2>/dev/null; then
    echo "✓ 'messenger' module found, starting server..."
    exec gunicorn messenger.asgi:application \
        --bind 0.0.0.0:10000 \
        --workers 2 \
        --worker-class gthread \
        --threads 4 \
        --timeout 120 \
        --access-logfile -
elif python -c "import messenger_app" 2>/dev/null; then
    echo "✓ 'messenger_app' module found, trying alternative path..."
    exec gunicorn messenger_app.messenger.asgi:application \
        --bind 0.0.0.0:10000 \
        --workers 2 \
        --worker-class gthread \
        --threads 4 \
        --timeout 120 \
        --access-logfile -
else
    echo "✗ ERROR: Could not find messenger or messenger_app module"
    echo "Listing Python modules:"
    python -c "import sys; print([m for m in sys.modules if 'messenger' in m])"
    echo "Trying to import with debug..."
    python -c "
import sys
print('Python path:', sys.path)
try:
    import messenger
    print('Successfully imported messenger')
except ImportError as e:
    print('Failed to import messenger:', e)
    print('Trying messenger_app...')
    try:
        import messenger_app
        print('Successfully imported messenger_app')
    except ImportError as e2:
        print('Failed to import messenger_app:', e2)
    "
    exit 1
fi