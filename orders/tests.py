from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class OrderViewsTest(TestCase):
    """Тесты заказов."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        self.client = Client()
        self.client.login(username='testuser', password='TestPass123!')

    def test_order_history_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('orders:history'), follow=True)
        self.assertRedirects(response, f"{reverse('users:login')}?next={reverse('orders:history')}")
