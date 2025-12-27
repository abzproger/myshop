from django.test import TestCase
from celery import current_app

from catalog.tasks import ping


class CeleryPingTest(TestCase):
    def test_ping_runs_in_eager_mode(self):
        """Проверяем, что задача Celery доступна и выполняется."""
        app = current_app
        prev_eager = app.conf.task_always_eager
        prev_prop = app.conf.task_eager_propagates
        try:
            app.conf.task_always_eager = True
            app.conf.task_eager_propagates = True
            result = ping.delay()
            self.assertEqual(result.get(timeout=5), "pong")
        finally:
            app.conf.task_always_eager = prev_eager
            app.conf.task_eager_propagates = prev_prop
