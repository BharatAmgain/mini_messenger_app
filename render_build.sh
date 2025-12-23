#!/bin/bash
# render_build.sh - ULTIMATE FIX

echo "🔧 Starting Render build process..."

# Clean up any existing builds
echo "🧹 Cleaning up..."
rm -rf __pycache__ */__pycache__

# Install with verbose output
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir

# Verify installations
echo "✅ Installed packages:"
pip list | grep -E "(Django|gunicorn|psycopg|channels|daphne)"

echo "🎉 Build completed successfully!"