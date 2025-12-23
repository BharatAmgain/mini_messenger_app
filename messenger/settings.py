# messenger/settings.py - COMPLETE FIXED VERSION
import os
import sys
from pathlib import Path
from decouple import config, Csv
import dj_database_url
import logging.config

BASE_DIR = Path(__file__).resolve().parent.parent

# Add apps directory to Python path
sys.path.append(str(BASE_DIR / 'apps'))

# Secret Key - Load from environment
SECRET_KEY = config('SECRET_KEY', default='django-insecure-development-key-change-this-in-production')

# Debug Mode
DEBUG = config('DEBUG', default=False, cast=bool)

# Allowed Hosts - Load from environment
ALLOWED_HOSTS = config('ALLOWED_HOSTS',
                       default='localhost,127.0.0.1,connect-io-0cql.onrender.com',
                       cast=Csv()
                       )

# CSRF Trusted Origins - Load from environment
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS',
                              default='https://connect-io-0cql.onrender.com,http://localhost:8000,http://127.0.0.1:8000',
                              cast=Csv()
                              )

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

# ========== DATABASE CONFIGURATION ==========
# Get DATABASE_URL from environment
DATABASE_URL = config('DATABASE_URL', default='sqlite:///db.sqlite3')

# Auto-detect database type and configure accordingly
if DATABASE_URL.startswith('postgres://'):
    # Convert postgres:// to postgresql:// for dj_database_url
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

if DATABASE_URL.startswith('sqlite:///'):
    # SQLite configuration
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
    # PostgreSQL configuration (for Render)
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
LANGUAGE_CODE = config('LANGUAGE_CODE', default='en-us')
TIME_ZONE = config('TIME_ZONE', default='Asia/Kathmandu')
USE_I18N = True
USE_L10N = True
USE_TZ = True

# ========== STATIC FILES FIXED SECTION ==========
# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise for static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Channels Configuration
REDIS_URL = config('REDIS_URL', default='redis://localhost:6379')
if DEBUG and 'RENDER' not in os.environ:
    # Use InMemoryChannelLayer for local development
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }
    print("✅ Using InMemoryChannelLayer for local development")
else:
    # Use Redis for production
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

# Custom User Model
AUTH_USER_MODEL = 'accounts.CustomUser'

# Authentication URLs
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'chat_home'
LOGOUT_REDIRECT_URL = 'login'

# ========== SENDGRID EMAIL CONFIGURATION ==========
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.sendgrid.net')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='apikey')  # LITERAL 'apikey'
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@connect.io')
EMAIL_TIMEOUT = config('EMAIL_TIMEOUT', default=30, cast=int)
EMAIL_SUBJECT_PREFIX = config('EMAIL_SUBJECT_PREFIX', default='[Connect.io] ')

print(f"\n📧 EMAIL CONFIGURATION:")
print(f"   Backend: {EMAIL_BACKEND}")
print(f"   Host: {EMAIL_HOST}")
print(f"   User: {EMAIL_HOST_USER}")

# Check SendGrid configuration
if 'sendgrid' in EMAIL_HOST:
    if EMAIL_HOST_PASSWORD and EMAIL_HOST_PASSWORD.startswith('SG.'):
        print("✅ SendGrid API Key configured")
        print(f"   Password: {'*' * 20}...{EMAIL_HOST_PASSWORD[-4:]}")
    else:
        print("❌ SENDGRID ERROR: Invalid API Key!")
        print("💡 Your API key should start with 'SG.'")
        if not EMAIL_HOST_PASSWORD:
            print("💡 EMAIL_HOST_PASSWORD is empty!")
        elif EMAIL_HOST_USER != 'apikey':
            print("💡 EMAIL_HOST_USER must be 'apikey' (literal)")
elif DEBUG and 'console' in EMAIL_BACKEND:
    print("✅ Development: Using console backend")
    print("   Emails will print to terminal")
else:
    print("⚠️  Unknown email configuration")

# Site Information
SITE_NAME = config('SITE_NAME', default='Connect.io')
SITE_DOMAIN = config('SITE_DOMAIN', default='connect-io-0cql.onrender.com')
ADMIN_EMAIL = config('ADMIN_EMAIL', default='admin@connect.io')
SUPPORT_EMAIL = config('SUPPORT_EMAIL', default='support@connect.io')

# CORS Configuration
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS',
                              default='http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000,http://127.0.0.1:8000',
                              cast=Csv()
                              )
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = config('CORS_ALLOW_METHODS',
                            default='DELETE,GET,OPTIONS,PATCH,POST,PUT',
                            cast=Csv())
CORS_ALLOW_HEADERS = config('CORS_ALLOW_HEADERS',
                            default='accept,accept-encoding,authorization,content-type,dnt,origin,user-agent,x-csrftoken,x-requested-with',
                            cast=Csv())

# CSRF Configuration
CSRF_COOKIE_HTTPONLY = config('CSRF_COOKIE_HTTPONLY', default=False, cast=bool)
CSRF_COOKIE_SAMESITE = config('CSRF_COOKIE_SAMESITE', default='Lax')
CSRF_USE_SESSIONS = False
CSRF_FAILURE_VIEW = 'messenger.views.csrf_failure'
CSRF_COOKIE_NAME = 'csrftoken'
CSRF_HEADER_NAME = 'HTTP_X_CSRFTOKEN'
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS',
                              default='https://connect-io-0cql.onrender.com,http://localhost:8000,http://127.0.0.1:8000',
                              cast=Csv()
                              )

# Social Auth Configuration
AUTHENTICATION_BACKENDS = (
    'social_core.backends.google.GoogleOAuth2',
    'social_core.backends.facebook.FacebookOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)

# ========== GOOGLE OAUTH2 FIXED CONFIGURATION ==========
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = config('GOOGLE_OAUTH2_KEY', default='')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = config('GOOGLE_OAUTH2_SECRET', default='')

# CRITICAL FIX: FORCE CORRECT REDIRECT URI
if 'RENDER' in os.environ or not DEBUG:
    # Production - ALWAYS use https://connect-io-0cql.onrender.com/complete/google-oauth2/
    SOCIAL_AUTH_GOOGLE_OAUTH2_REDIRECT_URI = 'https://connect-io-0cql.onrender.com/complete/google-oauth2/'
    print(f"🚨 GOOGLE OAUTH: Using HARDCODED production redirect URI: {SOCIAL_AUTH_GOOGLE_OAUTH2_REDIRECT_URI}")
else:
    # Development
    SOCIAL_AUTH_GOOGLE_OAUTH2_REDIRECT_URI = 'http://127.0.0.1:8000/complete/google-oauth2/'
    print(f"🚨 GOOGLE OAUTH: Using HARDCODED local redirect URI: {SOCIAL_AUTH_GOOGLE_OAUTH2_REDIRECT_URI}")

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

# ========== TWILIO CONFIGURATION ==========
TWILIO_ACCOUNT_SID = config('TWILIO_ACCOUNT_SID', default='')
TWILIO_AUTH_TOKEN = config('TWILIO_AUTH_TOKEN', default='')
TWILIO_VERIFY_SERVICE_SID = config('TWILIO_VERIFY_SERVICE_SID', default='')
TWILIO_PHONE_NUMBER = config('TWILIO_PHONE_NUMBER', default='+15005550006')
TWILIO_TEST_PHONE_NUMBER = config('TWILIO_TEST_PHONE_NUMBER', default='+9779866399895')

# OTP Configuration
OTP_TWILIO_NO_DELIVERY = config('OTP_TWILIO_NO_DELIVERY', default=True, cast=bool)
OTP_TWILIO_CHALLENGE_MESSAGE = config('OTP_TWILIO_CHALLENGE_MESSAGE', default='Your verification code is {token}')
OTP_TWILIO_FROM = TWILIO_PHONE_NUMBER
OTP_TWILIO_ACCOUNT = TWILIO_ACCOUNT_SID
OTP_TWILIO_AUTH = TWILIO_AUTH_TOKEN
OTP_TWILIO_TOKEN_VALIDITY = config('OTP_TWILIO_TOKEN_VALIDITY', default=300, cast=int)
OTP_TOTP_ISSUER = SITE_NAME

print("\n" + "=" * 60)
print("TWILIO CONFIGURATION STATUS")
print("=" * 60)
print(f"Account SID: {TWILIO_ACCOUNT_SID}")
print(f"Auth Token: {'✅ SET' if TWILIO_AUTH_TOKEN else '❌ MISSING - SMS verification disabled'}")
print(f"Verify Service SID: {TWILIO_VERIFY_SERVICE_SID}")
print(f"Phone Number: {TWILIO_PHONE_NUMBER}")

if not TWILIO_AUTH_TOKEN:
    print("⚠️  SMS verification disabled (no auth token)")
    OTP_TWILIO_NO_DELIVERY = True
    print("✅ OTP_TWILIO_NO_DELIVERY set to True")
else:
    print("✅ Twilio credentials configured")
print("=" * 60 + "\n")

# File Upload Limits
DATA_UPLOAD_MAX_MEMORY_SIZE = config('DATA_UPLOAD_MAX_MEMORY_SIZE', default=2621440, cast=int)
FILE_UPLOAD_MAX_MEMORY_SIZE = config('FILE_UPLOAD_MAX_MEMORY_SIZE', default=2621440, cast=int)
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755

# Session Configuration
SESSION_COOKIE_AGE = config('SESSION_COOKIE_AGE', default=1209600, cast=int)
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=False, cast=bool)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = config('SESSION_COOKIE_SAMESITE', default='Lax')
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_EXPIRE_AT_BROWSER_CLOSE = config('SESSION_EXPIRE_AT_BROWSER_CLOSE', default=False, cast=bool)
SESSION_SAVE_EVERY_REQUEST = True

# CSRF Configuration
CSRF_COOKIE_AGE = config('CSRF_COOKIE_AGE', default=31449600, cast=int)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=False, cast=bool)
CSRF_COOKIE_HTTPONLY = config('CSRF_COOKIE_HTTPONLY', default=False, cast=bool)
CSRF_COOKIE_SAMESITE = config('CSRF_COOKIE_SAMESITE', default='Lax')
CSRF_FAILURE_VIEW = 'messenger.views.csrf_failure'

# Cache Configuration
CACHE_BACKEND = config('CACHE_BACKEND', default='django.core.cache.backends.locmem.LocMemCache')
CACHE_LOCATION = config('CACHE_LOCATION', default='redis://localhost:6379/1')
CACHE_TIMEOUT = config('CACHE_TIMEOUT', default=300, cast=int)

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

# Logging Configuration
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
    },
    'handlers': {
        'console': {
            'level': LOG_LEVEL,
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'debug.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': LOG_LEVEL,
            'propagate': True,
        },
        'django.request': {
            'handlers': ['console', 'file'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'accounts': {
            'handlers': ['console', 'file'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'chat': {
            'handlers': ['console', 'file'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'social': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else LOG_LEVEL,
            'propagate': False,
        },
        'social_core': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else LOG_LEVEL,
            'propagate': False,
        },
    },
}

# Create logs directory if it doesn't exist
log_dir = BASE_DIR / 'logs'
log_dir.mkdir(exist_ok=True)

# Application Settings
MESSAGE_RETENTION_DAYS = config('MESSAGE_RETENTION_DAYS', default=30, cast=int)
MAX_GROUP_MEMBERS = config('MAX_GROUP_MEMBERS', default=50, cast=int)
TYPING_INDICATOR_TIMEOUT = config('TYPING_INDICATOR_TIMEOUT', default=5, cast=int)
PAGINATION_SIZE = config('PAGINATION_SIZE', default=20, cast=int)
MAX_LOGIN_ATTEMPTS = config('MAX_LOGIN_ATTEMPTS', default=5, cast=int)
LOGIN_LOCKOUT_TIME = config('LOGIN_LOCKOUT_TIME', default=300, cast=int)
NOTIFICATION_RETENTION_DAYS = config('NOTIFICATION_RETENTION_DAYS', default=90, cast=int)

# Feature Flags
ENABLE_TWO_FACTOR = config('ENABLE_TWO_FACTOR', default=False, cast=bool)
ENABLE_SOCIAL_AUTH = config('ENABLE_SOCIAL_AUTH', default=True, cast=bool)
ENABLE_FILE_UPLOADS = config('ENABLE_FILE_UPLOADS', default=True, cast=bool)
ENABLE_GROUP_CHATS = config('ENABLE_GROUP_CHATS', default=True, cast=bool)
ENABLE_PUSH_NOTIFICATIONS = config('ENABLE_PUSH_NOTIFICATIONS', default=False, cast=bool)
ENABLE_EMAIL_NOTIFICATIONS = config('ENABLE_EMAIL_NOTIFICATIONS', default=True, cast=bool)


# ========== DATABASE SETUP FUNCTION ==========
def ensure_migrations_and_user():
    """Run migrations and create test user automatically"""
    try:
        from django.core.management import execute_from_command_line
        from django.db import connections
        from django.db.utils import OperationalError

        print("=" * 50)
        print("STARTING DATABASE SETUP")
        print("=" * 50)

        # Try to connect to database
        try:
            connections['default'].ensure_connection()
            print("✅ Database connection successful")
        except OperationalError as e:
            print(f"⚠️  Cannot connect to database: {e}")
            print("⚠️  Please check your database configuration")
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
        print("⚠️  Django might not be properly installed")
    except Exception as e:
        print(f"❌ Database setup error: {e}")


# ========== RENDER-SPECIFIC CONFIGURATION ==========
if 'RENDER' in os.environ:
    print("🌐 Running on Render - Applying production settings...")

    # Force production settings
    DEBUG = False
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year

    # Auto-add Render URL to allowed hosts
    render_host = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
    if render_host:
        ALLOWED_HOSTS.append(render_host)
        CSRF_TRUSTED_ORIGINS.append(f'https://{render_host}')
        print(f"✅ Added {render_host} to allowed hosts")

    # Use environment DATABASE_URL if available
    if os.environ.get('DATABASE_URL'):
        DATABASE_URL = os.environ['DATABASE_URL']
        print("✅ Using Render PostgreSQL database from environment")

    # Force HTTPS for OAuth redirects on Render
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SOCIAL_AUTH_REDIRECT_IS_HTTPS = True

    # CRITICAL: Check SendGrid configuration for Render
    print("\n📧 Checking SendGrid configuration for Render...")

    if 'sendgrid' in EMAIL_HOST:
        if EMAIL_HOST_PASSWORD and EMAIL_HOST_PASSWORD.startswith('SG.'):
            print("✅ SendGrid properly configured for Render")
            print("✅ Password reset emails will work!")
        else:
            print("❌ SENDGRID CONFIGURATION ERROR!")
            print("💡 Add these to Render Environment Variables:")
            print("   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend")
            print("   EMAIL_HOST=smtp.sendgrid.net")
            print("   EMAIL_PORT=587")
            print("   EMAIL_USE_TLS=True")
            print("   EMAIL_HOST_USER=apikey")
            print("   EMAIL_HOST_PASSWORD=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")
            print("   DEFAULT_FROM_EMAIL=noreply@connect.io")
    else:
        print("⚠️  Not using SendGrid - password reset may fail")

# Local development
else:
    print("💻 Running in local development mode...")

    # Development settings
    if DEBUG:
        print("🔧 DEBUG mode enabled - showing detailed errors")
        if 'console' in EMAIL_BACKEND:
            print("📧 Development: Using console backend - emails print to terminal")
        CORS_ALLOW_ALL_ORIGINS = True

# Security settings
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)
SECURE_HSTS_SECONDS = 0 if DEBUG else 31536000

print(f"\n✅ Settings loaded: DEBUG={DEBUG}, DATABASE={DATABASES['default']['ENGINE']}")
print(f"✅ Email Backend: {EMAIL_BACKEND}")

# Final password reset status
if 'RENDER' in os.environ:
    if 'sendgrid' in EMAIL_HOST and EMAIL_HOST_PASSWORD and EMAIL_HOST_PASSWORD.startswith('SG.'):
        print("✅ PASSWORD RESET: Will work on production with SendGrid!")
    else:
        print("❌ PASSWORD RESET: Will fail - SendGrid not configured")
else:
    if 'console' in EMAIL_BACKEND:
        print("✅ PASSWORD RESET: Will work locally (emails to console)")
    elif 'sendgrid' in EMAIL_HOST:
        print("✅ PASSWORD RESET: Using SendGrid for local testing")

# ========== DEBUG OUTPUT FOR GOOGLE OAUTH ==========
print("\n" + "=" * 80)
print("GOOGLE OAUTH CONFIGURATION STATUS - FIXED VERSION")
print("=" * 80)
print(f"🎯 Client ID: {'✅ SET' if SOCIAL_AUTH_GOOGLE_OAUTH2_KEY else '❌ MISSING'}")
print(f"🔑 Client Secret: {'✅ SET' if SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET else '❌ MISSING'}")
print(f"🔄 Redirect URI: {SOCIAL_AUTH_GOOGLE_OAUTH2_REDIRECT_URI}")
print(f"🌍 Environment: {'Render (Production)' if 'RENDER' in os.environ else 'Local (Development)'}")
print(f"🔗 Expected Google Console URI: https://connect-io-0cql.onrender.com/complete/google-oauth2/")
print("=" * 80)

# ========== SOCIAL AUTH DEBUGGING ==========
if DEBUG:
    # Enable social auth debugging in development
    SOCIAL_AUTH_LOG_LEVEL = 'DEBUG'
    print("\n🔧 Social Auth debugging enabled")

# ========== ERROR HANDLERS CONFIGURATION ==========
# Add these error handlers (CRITICAL FIX for your current issue)
handler404 = 'messenger.views.page_not_found'
handler500 = 'messenger.views.server_error'
handler403 = 'messenger.views.permission_denied'
handler400 = 'messenger.views.bad_request'

print("\n" + "=" * 60)
print("ERROR HANDLERS CONFIGURATED")
print("=" * 60)
print("✅ 404 Handler: messenger.views.page_not_found")
print("✅ 500 Handler: messenger.views.server_error")
print("✅ 403 Handler: messenger.views.permission_denied")
print("✅ 400 Handler: messenger.views.bad_request")
print("✅ CSRF Failure: messenger.views.csrf_failure")
print("=" * 60)

# ========== CREATE DIRECTORIES ON STARTUP ==========
# Create necessary directories
print("\n📁 Creating necessary directories...")
for directory in [STATIC_ROOT, MEDIA_ROOT, BASE_DIR / 'logs', BASE_DIR / 'static' / 'images', BASE_DIR / 'static' / 'js']:
    directory.mkdir(exist_ok=True, parents=True)
    print(f"✅ Created directory: {directory}")

# ========== RUN DATABASE SETUP ==========
# Run database setup on startup
if __name__ == 'messenger.settings':
    ensure_migrations_and_user()

    # ========== CRITICAL FIX FOR RENDER ==========
    if 'RENDER' in os.environ:
        # Force production settings for Render
        print("🚨 RENDER DETECTED - APPLYING PRODUCTION SETTINGS")

        # Security settings
        DEBUG = False
        SECURE_SSL_REDIRECT = True
        SESSION_COOKIE_SECURE = True
        CSRF_COOKIE_SECURE = True
        SECURE_HSTS_SECONDS = 31536000
        SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

        # Auto-detect Render hostname
        RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
        if RENDER_EXTERNAL_HOSTNAME:
            ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
            CSRF_TRUSTED_ORIGINS.append(f'https://{RENDER_EXTERNAL_HOSTNAME}')
            print(f"✅ Added {RENDER_EXTERNAL_HOSTNAME} to allowed hosts")

        # Static files on Render
        STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
        STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

        print(f"✅ Configured for Render with hostname: {RENDER_EXTERNAL_HOSTNAME}")
    else:
        print("💻 Running in local development mode")

    print("\n" + "=" * 60)
    print("DEPLOYMENT CONFIGURATION COMPLETE")
    print("=" * 60)
    print(f"🔧 DEBUG: {DEBUG}")
    print(f"🌍 ALLOWED_HOSTS: {ALLOWED_HOSTS}")
    print(f"🛡️ CSRF_TRUSTED_ORIGINS: {CSRF_TRUSTED_ORIGINS}")
    print(f"💾 DATABASE: {DATABASES['default']['ENGINE']}")
    print(f"📧 EMAIL: {EMAIL_BACKEND}")
    print("=" * 60)