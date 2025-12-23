#!/bin/bash

echo "Starting deployment setup..."

# Make migrations
python manage.py makemigrations accounts
python manage.py makemigrations chat

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Create superuser if not exists (for development)
echo "Creating superuser..."
echo "from django.contrib.auth import get_user_model; User = get_user_model(); \
User.objects.create_superuser('admin', 'admin@example.com', 'password') if not User.objects.filter(username='admin').exists() else None" | python manage.py shell

echo "✅ Deployment setup complete!"