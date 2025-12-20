#!/bin/bash
# cleanup.sh - Remove sensitive files

echo "🔒 Starting security cleanup..."

# Remove sensitive Python files
rm -f test_twilio_api.py fix_twilio_import.py fix_is_verified.py
rm -f twilio_config_template.py twilio_config.py

# Remove old .env files
rm -f .env.clean .env.example .env.backup

# Remove cache files
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type f -name "*.pyd" -delete
find . -type f -name ".coverage" -delete
find . -type d -name ".pytest_cache" -exec rm -rf {} +
find . -type d -name ".mypy_cache" -exec rm -rf {} +

# Remove IDE files
rm -rf .vscode/ .idea/ .vs/

# Remove OS files
find . -name ".DS_Store" -delete
find . -name "Thumbs.db" -delete
find . -name "desktop.ini" -delete

# Remove temp files
rm -rf tmp/ temp/ cache/ .cache/

# Check if .env is in .gitignore
if ! grep -q "^\.env$" .gitignore; then
    echo ".env" >> .gitignore
    echo "✅ Added .env to .gitignore"
fi

# Verify cleanup
echo ""
echo "✅ Cleanup completed!"
echo ""
echo "Remaining files to check:"
ls -la | grep -E "\.(env|key|secret|token|pem|crt|cer)"

echo ""
echo "⚠️  IMPORTANT: Rotate your Twilio Auth Token immediately!"
echo "   Go to: https://www.twilio.com/console"
echo "   Settings → General → Regenerate Auth Token"