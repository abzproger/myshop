import os

from celery import Celery

# Указываем Django настройки перед созданием Celery приложения
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shop.settings")

app = Celery("shop")

# Читаем конфиг из Django settings с префиксом CELERY_
app.config_from_object("django.conf:settings", namespace="CELERY")

# Авто-поиск tasks.py во всех INSTALLED_APPS
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    # Упрощённая диагностическая задача
    print(f"Request: {self.request!r}")

