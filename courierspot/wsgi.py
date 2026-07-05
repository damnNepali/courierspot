"""
WSGI config for courierspot project.

"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'courierspot.settings')

application = get_wsgi_application()
