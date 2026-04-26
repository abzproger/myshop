from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class HealthcheckTests(TestCase):
    def test_healthcheck_returns_ok(self):
        response = self.client.get(reverse("healthz"))

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"status": "ok"})


class AdminSmokeTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="AdminPass123!",
        )
        self.client.force_login(self.user)

    def test_admin_index_uses_project_branding(self):
        response = self.client.get(reverse("admin:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SofaArt Admin")
