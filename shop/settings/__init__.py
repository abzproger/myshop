"""
Точка входа `shop.settings` — то же, что `shop.settings.local`.

Явно: `DJANGO_SETTINGS_MODULE=shop.settings.prod` для продакшена (WSGI по умолчанию
уже подключает prod; для Celery см. docker-compose).
"""

from .local import *  # noqa: F403
