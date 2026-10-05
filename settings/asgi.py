import os

from django.core.asgi import get_asgi_application

from settings.conf import ENV_ID, ENV_ID_LOCAL, ENV_ID_PROD

SETTINGS_MODULES = {
    ENV_ID_LOCAL: 'settings.env.local',
    ENV_ID_PROD: 'settings.env.prod',
}

os.environ['DJANGO_SETTINGS_MODULE'] = SETTINGS_MODULES[ENV_ID]

application = get_asgi_application()