# messenger/settings.py

import os
from pathlib import Path
from decouple import config

# --------------------------------------------------
# BASE CONFIG
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')

DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = ['mini-messenger-app.onrender.com']

# --------------------------------------------------
# APPLICATIONS
# --------------------------------------------------

INSTALLED_APPS = [
    'daphne',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'channels',

    'accounts',
    'chat',

    'social_django',
]

# --------------------------------------------------
# MIDDLEWARE
# --------------------------------------------------

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',

    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'social_django.middleware.SocialAuthExceptionMiddleware',
]

# --------------------------------------------------
# URL / TEMPLATE CONFIG
# --------------------------------------------------

ROOT_URLCONF = 'messenger.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',   # REQUIRED
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',

                # Social auth
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
        },
    },
]

# --------------------------------------------------
# DATABASE
# --------------------------------------------------

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# --------------------------------------------------
# PASSWORD VALIDATION
# --------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8}
    },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --------------------------------------------------
# INTERNATIONALIZATION
# --------------------------------------------------

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kathmandu'
USE_I18N = True
USE_TZ = True

# --------------------------------------------------
# STATIC & MEDIA FILES
# --------------------------------------------------

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# --------------------------------------------------
# DEFAULT PRIMARY KEY
# --------------------------------------------------

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --------------------------------------------------
# AUTH CONFIG
# --------------------------------------------------

AUTH_USER_MODEL = 'accounts.CustomUser'

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'chat_home'
LOGOUT_REDIRECT_URL = 'login'

# --------------------------------------------------
# EMAIL (DEV)
# --------------------------------------------------

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'noreply@connect.io'

# --------------------------------------------------
# CHANNELS / ASGI
# --------------------------------------------------

ASGI_APPLICATION = 'messenger.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    }
}

# --------------------------------------------------
# SOCIAL AUTH
# --------------------------------------------------

AUTHENTICATION_BACKENDS = (
    'social_core.backends.google.GoogleOAuth2',
    'social_core.backends.facebook.FacebookOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)

SOCIAL_AUTH_JSONFIELD_ENABLED = True

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = config('GOOGLE_OAUTH2_KEY', default='')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = config('GOOGLE_OAUTH2_SECRET', default='')

SOCIAL_AUTH_FACEBOOK_KEY = config('FACEBOOK_APP_ID', default='')
SOCIAL_AUTH_FACEBOOK_SECRET = config('FACEBOOK_APP_SECRET', default='')
SOCIAL_AUTH_FACEBOOK_SCOPE = ['email', 'public_profile']
SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {
    'fields': 'id,name,email,picture.type(large)',
}

SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
    'accounts.pipeline.save_profile_picture',
)

SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/chat/'
SOCIAL_AUTH_LOGIN_ERROR_URL = '/accounts/login/'
SOCIAL_AUTH_NEW_USER_REDIRECT_URL = '/chat/'

# --------------------------------------------------
# SECURITY (RENDER SAFE)
# --------------------------------------------------

CSRF_TRUSTED_ORIGINS = [
    'https://mini-messenger-app.onrender.com',
]

if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

    # IMPORTANT: keep False on Render
    SECURE_SSL_REDIRECT = False

    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
