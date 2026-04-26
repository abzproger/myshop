"""Продакшен: WSGI/ASGI по умолчанию, Celery в Docker (см. docker-compose)."""

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403
from ._post_debug import apply_production_security

DEBUG = env.bool("DJANGO_DEBUG", default=False)

_allowed = env("DJANGO_ALLOWED_HOSTS", default="")
ALLOWED_HOSTS = [h.strip() for h in _allowed.split(",") if h.strip()]
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured("Укажите DJANGO_ALLOWED_HOSTS для продакшен-конфигурации.")

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

apply_production_security(env, globals())
