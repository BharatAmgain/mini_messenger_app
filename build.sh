#!/usr/bin/env bash
# build.sh for Render - FINAL FIX VERSION

echo "🚀 Starting Render deployment with COMPLETE database fixes..."

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Run ALL migrations
echo "🔧 Running ALL database migrations..."
python manage.py migrate --no-input

# Apply emergency fixes for any missing columns
echo "🔧 Applying emergency database column fixes..."
python fix_production.py

echo "✅ Build completed successfully!"
echo "🎉 Application is ready for PUBLIC registration!"
echo "👉 Anyone can register at: https://connect-io-0cql.onrender.com/accounts/register/"