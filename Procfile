# Procfile
release: python manage.py migrate
web: daphne messenger.asgi:application --port $PORT --bind 0.0.0.0