from datetime import timedelta

from settings.conf import ALLOWED_HOSTS, BASE_DIR, SECRET_KEY  # noqa: F401

LOGS_DIR = BASE_DIR / 'logs'
LOG_FILE_NAME = 'blog.log'
LOG_LEVEL = 'INFO'

ACCESS_TOKEN_LIFETIME_MINUTES = 60
REFRESH_TOKEN_LIFETIME_DAYS = 7

INSTALLED_APPS = [
    'unfold',
    'unfold.contrib.filters',
    'unfold.contrib.forms',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'apps.auths',
    'apps.blog',
]

AUTH_USER_MODEL = 'auths.User'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'settings.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'settings.wsgi.application'
ASGI_APPLICATION = 'settings.asgi.application'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=ACCESS_TOKEN_LIFETIME_MINUTES),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=REFRESH_TOKEN_LIFETIME_DAYS),
    'AUTH_HEADER_TYPES': ('Bearer',),
}

UNFOLD = {
    'SITE_TITLE': 'Blog API',
    'SITE_HEADER': 'Blog API',
    'SITE_SUBHEADER': 'Content management',
    'SITE_SYMBOL': 'newspaper',
    'ENVIRONMENT': 'apps.blog.callbacks.environment_callback',
    'DASHBOARD_CALLBACK': 'apps.blog.callbacks.dashboard_callback',
    'COLORS': {
        'primary': {
            '50': '#f0f9ff',
            '100': '#e0f2fe',
            '200': '#bae6fd',
            '300': '#7dd3fc',
            '400': '#38bdf8',
            '500': '#0ea5e9',
            '600': '#0284c7',
            '700': '#0369a1',
            '800': '#075985',
            '900': '#0c4a6e',
            '950': '#082f49',
        },
    },
    'SITE_DROPDOWN': [
        {
            'icon': 'code',
            'title': 'GitHub repository',
            'link': 'https://github.com/birzhaaan/blog-api',
        },
        {
            'icon': 'menu_book',
            'title': 'Unfold documentation',
            'link': 'https://unfoldadmin.com/docs/',
        },
    ],
    'COMMAND': {
        'search_models': True,
        'show_history': True,
    },
    'SIDEBAR': {
        'show_search': True,
        'show_all_applications': False,
        'navigation': 'apps.blog.callbacks.navigation_callback',
    },
    'TABS': 'apps.blog.callbacks.tabs_callback',
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {'format': '{asctime} {levelname} {name} {message}', 'style': '{'},
    },
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': LOGS_DIR / LOG_FILE_NAME,
            'formatter': 'default',
        },
    },
    'root': {'handlers': ['file'], 'level': LOG_LEVEL},
}