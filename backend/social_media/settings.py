# settings.py
from pathlib import Path
import os
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = 'django-insecure-hs88%e(wz^$8%b#jh=9)q9#k!cimzggveahcw5#l72%1sfv6#x'
SECRET_KEY = os.getenv("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False


ALLOWED_HOSTS = ["192.168.2.239","127.0.0.1","localhost"]

AUTHENTICATION_BACKENDS = [
    'users.auth_backend.LoggingModelBackend',
    # 'django.contrib.auth.backends.ModelBackend',
]

CSRF_TRUSTED_ORIGINS = ["https://192.168.2.239"]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'users',
    'friends',
    'messaging',
    'marketplace',
    'captcha',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'users.middleware.LoginAttemptMiddleware',
    'users.middleware.AuthenticationMiddleware',
]

ROOT_URLCONF = 'social_media.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'users.context_processors.notification_count',
                'users.context_processors.cart_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'social_media.wsgi.application'

load_dotenv()  # Load environment variables

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'db'),  # Use "db" (same as service name in Docker)
        #'HOST': '127.0.0.1', 
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'"
        }
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MEDIA_URL = '/protected-media/'
# MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Auth user model
AUTH_USER_MODEL = 'users.CustomUser'

# Encryption key for message encryption (generate a secure key for production)
ENCRYPTION_KEY =os.getenv("ENCRYPTION_KEY")
# Login URLs
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'profile'
LOGOUT_REDIRECT_URL = 'login'

# Add these to your settings.py
SESSION_COOKIE_AGE = 1800  # 30 secs
SESSION_COOKIE_SECURE = True  # Set to True in production with HTTPS  

# Production m on krna hai 
SESSION_COOKIE_SECURE = True     # Only send session cookies over HTTPS
CSRF_COOKIE_SECURE = True        # Only send CSRF token over HTTPS
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_SSL_REDIRECT = True  # Only if Nginx is handling HTTPS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')    # Redirect all HTTP to HTTPS (after HTTPS is working!)
