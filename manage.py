#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

from settings.conf import ENV_ID, ENV_ID_LOCAL, ENV_ID_PROD

SETTINGS_MODULES = {
    ENV_ID_LOCAL: 'settings.env.local',
    ENV_ID_PROD: 'settings.env.prod',
}


def main() -> None:
    """Run administrative tasks."""
    os.environ['DJANGO_SETTINGS_MODULE'] = SETTINGS_MODULES[ENV_ID]
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Is it installed and is the venv activated?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()