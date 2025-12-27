from celery import shared_task


@shared_task
def ping():
    """Простая проверочная задача Celery."""
    return "pong"

