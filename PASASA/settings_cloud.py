"""EC2 settings. systemd supplies /etc/pasasa/.env via EnvironmentFile."""
import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured


def required(name):
    value = os.environ.get(name, '').strip()
    if not value:
        raise ImproperlyConfigured(f'Set {name} in the service EnvironmentFile.')
    return value


os.environ.setdefault('DJANGO_DEBUG', '0')
if os.environ['DJANGO_DEBUG'] != '0':
    raise ImproperlyConfigured('DJANGO_DEBUG must be 0 for cloud settings.')
required('DJANGO_SECRET_KEY')
cloud_hosts = [host.strip() for host in required('DJANGO_ALLOWED_HOSTS').split(',') if host.strip()]
if not cloud_hosts or '*' in cloud_hosts:
    raise ImproperlyConfigured('DJANGO_ALLOWED_HOSTS must contain explicit host names.')

from .settings import *  # noqa: E402,F403

DEBUG = False
ALLOWED_HOSTS = cloud_hosts
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': required('POSTGRES_DB'),
        'USER': required('POSTGRES_USER'),
        'PASSWORD': required('POSTGRES_PASSWORD'),
        'HOST': required('POSTGRES_HOST'),
        'PORT': required('POSTGRES_PORT'),
        'CONN_MAX_AGE': 60,
        'CONN_HEALTH_CHECKS': True,
        'OPTIONS': {'connect_timeout': 5},
    },
}
STATIC_ROOT = Path(os.environ.get('DJANGO_STATIC_ROOT', '/var/lib/pasasa/static'))
MEDIA_ROOT = Path(os.environ.get('DJANGO_MEDIA_ROOT', '/var/lib/pasasa/media'))

# Nginx replaces this header and Gunicorn listens only on loopback.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
HTTPS_ENABLED = os.environ.get('DJANGO_HTTPS', '1') == '1'
SECURE_SSL_REDIRECT = HTTPS_ENABLED
SESSION_COOKIE_SECURE = HTTPS_ENABLED
CSRF_COOKIE_SECURE = HTTPS_ENABLED
SECURE_HSTS_SECONDS = 3600 if HTTPS_ENABLED else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
CSRF_TRUSTED_ORIGINS = [value.strip() for value in os.environ.get('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',') if value.strip()]
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'root': {'handlers': ['console'], 'level': 'INFO'},
}
