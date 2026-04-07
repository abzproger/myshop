"""Локальная разработка: runserver, тесты, `manage.py` по умолчанию (`shop.settings`)."""

from .base import *  # noqa: F403
from ._post_debug import apply_production_security

DEBUG = env.bool("DJANGO_DEBUG", default=True)

_allowed = env("DJANGO_ALLOWED_HOSTS", default="127.0.0.1,localhost")
ALLOWED_HOSTS = [h.strip() for h in _allowed.split(",") if h.strip()]

apply_production_security(env, globals())
