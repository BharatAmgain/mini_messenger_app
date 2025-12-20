# messenger/settings.py - COMPLETE WITH ALL MOBILE OPTIMIZATIONS
import os
import sys
from pathlib import Path
from decouple import config, Csv
import dj_database_url
import logging.config
from datetime import timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Add apps directory to Python path
sys.path.append(str(BASE_DIR / 'apps'))

# Quick-start development settings
SECRET_KEY = config('SECRET_KEY', default='django-insecure-development-key-change-this-in-production')

# Debug mode
DEBUG = config('DEBUG', default=True, cast=bool)

# Allowed hosts
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='localhost,127.0.0.1,connect-io-0cql.onrender.com',
    cast=Csv()
)

# CSRF trusted origins
CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='https://connect-io-0cql.onrender.com,http://localhost:8000,http://127.0.0.1:8000',
    cast=Csv()
)

# Application definition
INSTALLED_APPS = [
    # Daphne for ASGI
    'daphne',

    # Django core apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    # Third party apps
    'channels',
    'corsheaders',
    'social_django',
    'otp_twilio',
    'django_otp',
    'django_otp.plugins.otp_totp',
    'django_otp.plugins.otp_static',

    # Local apps
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

    # Custom middleware
    'messenger.middleware.MobileMiddleware',
]

# Site ID
SITE_ID = 1

# Root URL config
ROOT_URLCONF = 'messenger.urls'

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
            BASE_DIR / 'templates' / 'errors',
        ],
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
            'builtins': [
                'chat.templatetags.chat_filters',
            ],
        },
    },
]

# WSGI & ASGI
WSGI_APPLICATION = 'messenger.wsgi.application'
ASGI_APPLICATION = 'messenger.asgi.application'

# Database
DATABASE_URL = config('DATABASE_URL', default='sqlite:///db.sqlite3')

# Auto-detect database type
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

if DATABASE_URL.startswith('sqlite:///'):
    # SQLite for local development
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
            'OPTIONS': {
                'timeout': 20,
            }
        }
    }
    print("✅ Using SQLite database for local development")
else:
    # PostgreSQL for production
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=True,
        )
    }
    DATABASES['default']['ENGINE'] = 'django.db.backends.postgresql'
    print("✅ Using PostgreSQL database for production")

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
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
LANGUAGE_CODE = config('LANGUAGE_CODE', default='en-us')
TIME_ZONE = config('TIME_ZONE', default='Asia/Kathmandu')
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
    BASE_DIR / 'chat' / 'static',
    BASE_DIR / 'accounts' / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Create directories if they don't exist
os.makedirs(MEDIA_ROOT, exist_ok=True)
os.makedirs(MEDIA_ROOT / 'profile_pics', exist_ok=True)
os.makedirs(MEDIA_ROOT / 'group_photos', exist_ok=True)
os.makedirs(MEDIA_ROOT / 'message_files', exist_ok=True)
os.makedirs(MEDIA_ROOT / 'uploads', exist_ok=True)
os.makedirs(BASE_DIR / 'logs', exist_ok=True)

# Default primary key
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Channels configuration
REDIS_URL = config('REDIS_URL', default='redis://localhost:6379')

if DEBUG and 'RENDER' not in os.environ:
    # InMemoryChannelLayer for local development
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }
    print("✅ Using InMemoryChannelLayer for local development")
else:
    # Redis for production
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
    print("✅ Using Redis ChannelLayer")

# Custom user model
AUTH_USER_MODEL = 'accounts.CustomUser'

# Authentication URLs
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'chat_home'
LOGOUT_REDIRECT_URL = 'login'

# Email configuration
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.sendgrid.net')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='apikey')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@connect.io')
EMAIL_TIMEOUT = config('EMAIL_TIMEOUT', default=30, cast=int)
EMAIL_SUBJECT_PREFIX = config('EMAIL_SUBJECT_PREFIX', default='[Connect.io] ')

# Site information
SITE_NAME = config('SITE_NAME', default='Connect.io')
SITE_DOMAIN = config('SITE_DOMAIN', default='connect-io-0cql.onrender.com')
ADMIN_EMAIL = config('ADMIN_EMAIL', default='admin@connect.io')
SUPPORT_EMAIL = config('SUPPORT_EMAIL', default='support@connect.io')

# CORS configuration for mobile
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000,http://127.0.0.1:8000',
    cast=Csv()
)
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
    'x-device-type',
    'x-screen-width',
]

# CSRF configuration for mobile
CSRF_COOKIE_HTTPONLY = False  # Allow JavaScript access for mobile
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_USE_SESSIONS = False
CSRF_FAILURE_VIEW = 'messenger.views.csrf_failure'
CSRF_COOKIE_NAME = 'csrftoken'
CSRF_HEADER_NAME = 'HTTP_X_CSRFTOKEN'

# Social auth configuration
AUTHENTICATION_BACKENDS = (
    'social_core.backends.google.GoogleOAuth2',
    'social_core.backends.facebook.FacebookOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)

# Google OAuth2
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = config('GOOGLE_OAUTH2_KEY', default='')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = config('GOOGLE_OAUTH2_SECRET', default='')
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
SOCIAL_AUTH_FACEBOOK_KEY = config('FACEBOOK_APP_ID', default='')
SOCIAL_AUTH_FACEBOOK_SECRET = config('FACEBOOK_APP_SECRET', default='')
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
SOCIAL_AUTH_FACEBOOK_API_VERSION = 'v19.0'

# Social auth pipeline
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

# Twilio configuration
TWILIO_ACCOUNT_SID = config('TWILIO_ACCOUNT_SID', default='')
TWILIO_AUTH_TOKEN = config('TWILIO_AUTH_TOKEN', default='')
TWILIO_VERIFY_SERVICE_SID = config('TWILIO_VERIFY_SERVICE_SID', default='')
TWILIO_PHONE_NUMBER = config('TWILIO_PHONE_NUMBER', default='+15005550006')
TWILIO_TEST_PHONE_NUMBER = config('TWILIO_TEST_PHONE_NUMBER', default='+9779866399895')

# OTP configuration
OTP_TWILIO_NO_DELIVERY = config('OTP_TWILIO_NO_DELIVERY', default=True, cast=bool)
OTP_TWILIO_CHALLENGE_MESSAGE = config('OTP_TWILIO_CHALLENGE_MESSAGE', default='Your verification code is {token}')
OTP_TWILIO_FROM = TWILIO_PHONE_NUMBER
OTP_TWILIO_ACCOUNT = TWILIO_ACCOUNT_SID
OTP_TWILIO_AUTH = TWILIO_AUTH_TOKEN
OTP_TOTP_ISSUER = SITE_NAME

# File upload limits for mobile
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
MAX_UPLOAD_SIZE = 5242880  # 5MB
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755

# Session configuration for mobile
SESSION_COOKIE_AGE = 1209600  # 2 weeks
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=False, cast=bool)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # Keep session alive for mobile
SESSION_SAVE_EVERY_REQUEST = True

# Cache configuration
CACHE_BACKEND = config('CACHE_BACKEND', default='django.core.cache.backends.locmem.LocMemCache')
CACHE_LOCATION = config('CACHE_LOCATION', default='redis://localhost:6379/1')
CACHE_TIMEOUT = 300  # 5 minutes

CACHES = {
    'default': {
        'BACKEND': CACHE_BACKEND,
        'LOCATION': CACHE_LOCATION,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': config('CONNECTION_POOL_SIZE', default=10, cast=int),
            },
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'RETRY_ON_TIMEOUT': True,
        },
        'KEY_PREFIX': 'messenger',
        'TIMEOUT': CACHE_TIMEOUT,
    }
}

# Logging configuration
LOG_LEVEL = config('LOG_LEVEL', default='INFO')
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
        'mobile': {
            'format': '{asctime} [{levelname}] {message} [User: {user}, Device: {device}]',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': LOG_LEVEL,
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'error.log',
            'formatter': 'verbose',
        },
        'mobile_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'mobile.log',
            'formatter': 'mobile',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': True,
        },
        'django.request': {
            'handlers': ['console', 'file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'accounts': {
            'handlers': ['console', 'mobile_file'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'chat': {
            'handlers': ['console', 'mobile_file'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'mobile': {
            'handlers': ['console', 'mobile_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Application settings
MESSAGE_RETENTION_DAYS = config('MESSAGE_RETENTION_DAYS', default=30, cast=int)
MAX_GROUP_MEMBERS = config('MAX_GROUP_MEMBERS', default=50, cast=int)
TYPING_INDICATOR_TIMEOUT = config('TYPING_INDICATOR_TIMEOUT', default=5, cast=int)
PAGINATION_SIZE = config('PAGINATION_SIZE', default=20, cast=int)
MAX_LOGIN_ATTEMPTS = config('MAX_LOGIN_ATTEMPTS', default=5, cast=int)
LOGIN_LOCKOUT_TIME = config('LOGIN_LOCKOUT_TIME', default=300, cast=int)
NOTIFICATION_RETENTION_DAYS = config('NOTIFICATION_RETENTION_DAYS', default=90, cast=int)

# Feature flags
ENABLE_TWO_FACTOR = config('ENABLE_TWO_FACTOR', default=False, cast=bool)
ENABLE_SOCIAL_AUTH = config('ENABLE_SOCIAL_AUTH', default=True, cast=bool)
ENABLE_FILE_UPLOADS = config('ENABLE_FILE_UPLOADS', default=True, cast=bool)
ENABLE_GROUP_CHATS = config('ENABLE_GROUP_CHATS', default=True, cast=bool)
ENABLE_PUSH_NOTIFICATIONS = config('ENABLE_PUSH_NOTIFICATIONS', default=False, cast=bool)
ENABLE_EMAIL_NOTIFICATIONS = config('ENABLE_EMAIL_NOTIFICATIONS', default=True, cast=bool)

# Mobile-specific settings
MOBILE_USER_AGENTS = [
    'Android', 'iPhone', 'iPad', 'iPod', 'BlackBerry',
    'Windows Phone', 'webOS', 'Opera Mini', 'IEMobile'
]

# Security settings
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)
SECURE_HSTS_SECONDS = 0 if DEBUG else 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# Mobile optimization settings
MOBILE_CACHE_TIMEOUT = 300  # 5 minutes
MOBILE_SESSION_TIMEOUT = 3600  # 1 hour for mobile
MOBILE_MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Print configuration summary
print("\n" + "=" * 60)
print("CONNECT.IO MESSENGER - CONFIGURATION SUMMARY")
print("=" * 60)
print(f"✅ DEBUG Mode: {DEBUG}")
print(f"✅ Database: {DATABASES['default']['ENGINE']}")
print(f"✅ Email Backend: {EMAIL_BACKEND}")
print(f"✅ Mobile Support: ENABLED")
print(f"✅ File Upload Limit: {FILE_UPLOAD_MAX_MEMORY_SIZE / 1024 / 1024}MB")
print(f"✅ Session Timeout: {SESSION_COOKIE_AGE / 60 / 60 / 24} days")
print(f"✅ CORS Enabled: {len(CORS_ALLOWED_ORIGINS)} origins")
print("=" * 60 + "\n")

# Render-specific configuration
if 'RENDER' in os.environ:
    print("🌐 Running on Render - Applying production settings...")

    # Force production settings
    DEBUG = False
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000

    # Auto-add Render URL
    render_host = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
    if render_host:
        ALLOWED_HOSTS.append(render_host)
        CSRF_TRUSTED_ORIGINS.append(f'https://{render_host}')
        print(f"✅ Added {render_host} to allowed hosts")

    # Force HTTPS for OAuth
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SOCIAL_AUTH_REDIRECT_IS_HTTPS = True

    # Check SendGrid
    if 'sendgrid' in EMAIL_HOST and EMAIL_HOST_PASSWORD and EMAIL_HOST_PASSWORD.startswith('SG.'):
        print("✅ SendGrid properly configured")
    else:
        print("⚠️  SendGrid not configured - email features disabled")

# Local development
else:
    print("💻 Running in local development mode...")
    if DEBUG:
        CORS_ALLOW_ALL_ORIGINS = True
        ALLOWED_HOSTS = ['*']
        CSRF_TRUSTED_ORIGINS = ['http://localhost:8000', 'http://127.0.0.1:8000']


# Database setup function
def ensure_migrations_and_user():
    """Run migrations and create test user automatically"""
    try:
        from django.core.management import execute_from_command_line
        from django.db import connections
        from django.db.utils import OperationalError

        print("\n" + "=" * 50)
        print("STARTING DATABASE SETUP")
        print("=" * 50)

        # Try to connect to database
        try:
            connections['default'].ensure_connection()
            print("✅ Database connection successful")
        except OperationalError as e:
            print(f"⚠️  Cannot connect to database: {e}")
            return

        # Run migrations
        print("1. Running database migrations...")
        try:
            execute_from_command_line(['manage.py', 'migrate', '--no-input'])
            print("✅ Migrations completed")
        except Exception as e:
            print(f"❌ Migration error: {e}")
            return

        # Create test user
        print("2. Creating test user...")
        from django.contrib.auth import get_user_model
        User = get_user_model()

        try:
            if not User.objects.filter(email='test@example.com').exists():
                User.objects.create_user(
                    username='testuser',
                    email='test@example.com',
                    password='TestPass123!',
                    phone_number='+9779866399895',
                    is_verified=True
                )
                print("✅ Created test user: test@example.com / TestPass123!")
                print("✅ Phone number set: +9779866399895")
            else:
                print("✅ Test user already exists")
        except Exception as e:
            print(f"❌ Error creating test user: {e}")

        print("=" * 50)
        print("DATABASE SETUP COMPLETE")
        print("=" * 50)

    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Database setup error: {e}")


# Run database setup if flag is set
if os.environ.get('RUN_DATABASE_SETUP', 'False').lower() == 'true':
    ensure_migrations_and_user()