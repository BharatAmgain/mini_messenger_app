# messenger/settings.py
import os
import sys
from pathlib import Path
from decouple import config, Csv
import dj_database_url
import logging.config

BASE_DIR = Path(__file__).resolve().parent.parent

# Add apps directory to Python path
sys.path.append(str(BASE_DIR / 'apps'))

# Secret Key - CRITICAL: Generate a new one for production
SECRET_KEY = config('SECRET_KEY', default='django-insecure-79_MPQq2_F4ryVm17Fm81fJnzhI2uSxMlgyUKq0hAyaZTrhIJBl')

# Debug Mode - SET TO TRUE TO SEE ERRORS
DEBUG = True  # TEMPORARILY TRUE FOR DEBUGGING - CHANGE TO FALSE IN PRODUCTION

# Allowed Hosts - UPDATED WITH YOUR LATEST URL
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'connect-io-0cql.onrender.com',  # NEW URL
    'connect-io-lg60.onrender.com',
    'connect-io-dbwj.onrender.com',
    'mini-messenger-app.onrender.com',
    '*',  # TEMPORARY FOR TESTING - REMOVE IN PRODUCTION
]

# CSRF Trusted Origins - UPDATED
CSRF_TRUSTED_ORIGINS = [
    'https://connect-io-0cql.onrender.com',  # NEW URL
    'https://connect-io-lg60.onrender.com',
    'https://connect-io-dbwj.onrender.com',
    'https://mini-messenger-app.onrender.com',
]

# Installed Apps
INSTALLED_APPS = [
    'daphne',

    # Django Core Apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third Party Apps
    'channels',
    'corsheaders',
    'social_django',
    'otp_twilio',
    'django_otp',
    'django_otp.plugins.otp_totp',
    'django_otp.plugins.otp_static',

    # Local Apps
    'accounts',
    'chat',
]

# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware',
    'django_otp.middleware.OTPMiddleware',
]

# URL Configuration
ROOT_URLCONF = 'messenger.urls'

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
                'messenger.context_processors.site_info',
            ],
        },
    },
]

# WSGI & ASGI
WSGI_APPLICATION = 'messenger.wsgi.application'
ASGI_APPLICATION = 'messenger.asgi.application'

# Database - USING YOUR PROVIDED DATABASE URL
DATABASE_URL = 'postgresql://messenger_db_qgbv_user:sqo0VNUxDOIH5GI5hKUx8sqj1f9qeItT@dpg-d524vbali9vc73evrbfg-a/messenger_db_qgbv'

DATABASES = {
    'default': dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=600,
        conn_health_checks=True,
        ssl_require=True,
    )
}
# Ensure correct engine
DATABASES['default']['ENGINE'] = 'django.db.backends.postgresql'

# Password Validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        'OPTIONS': {
            'user_attributes': ('username', 'email', 'first_name', 'last_name'),
            'max_similarity': 0.7,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kathmandu'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static'] if os.path.exists(BASE_DIR / 'static') else []
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Channels Configuration
REDIS_URL = 'redis://localhost:6379'
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [REDIS_URL],
            "symmetric_encryption_keys": [SECRET_KEY],
            "capacity": 1500,
            "expiry": 10,
        },
    },
}

# Custom User Model
AUTH_USER_MODEL = 'accounts.CustomUser'

# Authentication URLs
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'chat_home'
LOGOUT_REDIRECT_URL = 'login'

# Email Configuration - SET TO CONSOLE FOR TESTING
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
DEFAULT_FROM_EMAIL = 'noreply@connect.io'
EMAIL_TIMEOUT = 30
EMAIL_SUBJECT_PREFIX = '[Connect.io] '

# Site Information - UPDATED
SITE_NAME = 'Connect.io'
SITE_DOMAIN = 'connect-io-0cql.onrender.com'  # NEW URL
ADMIN_EMAIL = 'admin@connect.io'
SUPPORT_EMAIL = 'support@connect.io'

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://localhost:8000',
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# CSRF Configuration - FIXED FOR AJAX REQUESTS
CSRF_COOKIE_HTTPONLY = False  # Allow JavaScript to read the CSRF token
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_USE_SESSIONS = False
CSRF_FAILURE_VIEW = 'messenger.views.csrf_failure'

# Social Auth Configuration
AUTHENTICATION_BACKENDS = (
    'social_core.backends.google.GoogleOAuth2',
    'social_core.backends.facebook.FacebookOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)

# Google OAuth2
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = ''
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = ''
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'openid'
]
SOCIAL_AUTH_GOOGLE_OAUTH2_AUTH_EXTRA_ARGUMENTS = {
    'access_type': 'online',
    'prompt': 'select_account',
}

# Facebook OAuth2
SOCIAL_AUTH_FACEBOOK_KEY = ''
SOCIAL_AUTH_FACEBOOK_SECRET = ''
SOCIAL_AUTH_FACEBOOK_SCOPE = ['email', 'public_profile']
SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {
    'fields': 'id,name,email,picture.type(large),first_name,last_name',
    'locale': 'en_US',
}
SOCIAL_AUTH_FACEBOOK_EXTRA_DATA = [
    ('name', 'name'),
    ('email', 'email'),
    ('picture', 'picture'),
    ('first_name', 'first_name'),
    ('last_name', 'last_name'),
]
SOCIAL_AUTH_FACEBOOK_API_VERSION = '12.0'

# Social Auth Pipeline
SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'accounts.pipeline.handle_duplicate_email',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
    'accounts.pipeline.save_profile_picture',
)

SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/chat/'
SOCIAL_AUTH_LOGIN_ERROR_URL = '/accounts/login/?error=auth'
SOCIAL_AUTH_NEW_USER_REDIRECT_URL = '/chat/'
SOCIAL_AUTH_URL_NAMESPACE = 'social'
SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL = False
SOCIAL_AUTH_USER_MODEL = 'accounts.CustomUser'
SOCIAL_AUTH_PROTECTED_USER_FIELDS = ['email', 'username']
SOCIAL_AUTH_RAISE_EXCEPTIONS = DEBUG
SOCIAL_AUTH_REDIRECT_IS_HTTPS = not DEBUG

# OTP Configuration
OTP_TWILIO_NO_DELIVERY = False
OTP_TWILIO_CHALLENGE_MESSAGE = 'Your verification code is {token}'
OTP_TWILIO_FROM = ''
OTP_TWILIO_ACCOUNT = ''
OTP_TWILIO_AUTH = ''
OTP_TWILIO_TOKEN_VALIDITY = 300
OTP_TOTP_ISSUER = SITE_NAME

# Twilio Configuration
TWILIO_ACCOUNT_SID = ''
TWILIO_AUTH_TOKEN = ''
TWILIO_PHONE_NUMBER = ''
TWILIO_VERIFY_SERVICE_SID = ''

# File Upload Limits
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755

# Session Configuration
SESSION_COOKIE_AGE = 1209600
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = True

# CSRF Configuration
CSRF_COOKIE_AGE = 31449600  # 1 year
CSRF_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_FAILURE_VIEW = 'messenger.views.csrf_failure'

# Cache Configuration
CACHE_BACKEND = 'django.core.cache.backends.redis.RedisCache'
CACHE_LOCATION = 'redis://localhost:6379/1'
CACHE_TIMEOUT = 300

CACHES = {
    'default': {
        'BACKEND': CACHE_BACKEND,
        'LOCATION': CACHE_LOCATION,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 10,
            },
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'RETRY_ON_TIMEOUT': True,
        },
        'KEY_PREFIX': 'messenger',
        'TIMEOUT': CACHE_TIMEOUT,
    }
}

# Logging Configuration - DETAILED FOR DEBUGGING
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',  # Changed from DEBUG to INFO
            'propagate': True,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'INFO',  # Changed from DEBUG to INFO
            'propagate': False,
        },
        'accounts': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'chat': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Create logs directory if it doesn't exist
log_dir = BASE_DIR / 'logs'
log_dir.mkdir(exist_ok=True)

# Application Settings
MESSAGE_RETENTION_DAYS = 30
MAX_GROUP_MEMBERS = 50
TYPING_INDICATOR_TIMEOUT = 5
PAGINATION_SIZE = 20
MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_TIME = 300
NOTIFICATION_RETENTION_DAYS = 90

# Feature Flags
ENABLE_TWO_FACTOR = False
ENABLE_SOCIAL_AUTH = True
ENABLE_FILE_UPLOADS = True
ENABLE_GROUP_CHATS = True
ENABLE_PUSH_NOTIFICATIONS = True
ENABLE_EMAIL_NOTIFICATIONS = True

# ========== CRITICAL FIX: AUTO-RUN MIGRATIONS ==========
# This ensures migrations run even without Shell access
import sys


def ensure_migrations_and_user():
    """Run migrations and create test user automatically"""
    try:
        from django.core.management import execute_from_command_line
        print("=" * 50)
        print("STARTING DATABASE SETUP")
        print("=" * 50)

        # Run migrations
        print("1. Running database migrations...")
        execute_from_command_line(['manage.py', 'migrate', '--no-input'])
        print("✅ Migrations completed")

        # Create test user
        print("2. Creating test user...")
        from django.contrib.auth import get_user_model
        User = get_user_model()

        if not User.objects.filter(email='test@example.com').exists():
            User.objects.create_user(
                username='testuser',
                email='test@example.com',
                password='TestPass123!',
                phone_number='+9779800000000',
                is_verified=True
            )
            print("✅ Created test user: test@example.com / TestPass123!")
        else:
            print("✅ Test user already exists")

        print("=" * 50)
        print("DATABASE SETUP COMPLETE")
        print("=" * 50)

    except Exception as e:
        print(f"❌ Database setup error: {e}")
        import traceback
        traceback.print_exc()


# Run setup when Django starts (for Render)
if 'RENDER' in os.environ or 'DATABASE_URL' in os.environ:
    ensure_migrations_and_user()

# ========== RENDER-SPECIFIC CONFIGURATION ==========
if 'RENDER' in os.environ:
    print("🌐 Running on Render - Applying production settings...")

    # Auto-add Render URL to allowed hosts
    render_host = os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'connect-io-0cql.onrender.com')
    if render_host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(render_host)
        CSRF_TRUSTED_ORIGINS.append(f'https://{render_host}')
        print(f"✅ Added {render_host} to allowed hosts")

    # Use environment DATABASE_URL if available
    if os.environ.get('DATABASE_URL'):
        DATABASES = {
            'default': dj_database_url.config(
                default=os.environ['DATABASE_URL'],
                conn_max_age=600,
                ssl_require=True,
            )
        }
        DATABASES['default']['ENGINE'] = 'django.db.backends.postgresql'
        print("✅ Using Render PostgreSQL database")

# Security settings - DISABLED FOR DEBUGGING
# Note: In production, set DEBUG=False and enable these
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0

# Development settings (when DEBUG=True)
if DEBUG:
    print("🔧 Running in DEBUG mode - showing detailed errors")
    CORS_ALLOW_ALL_ORIGINS = True
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'