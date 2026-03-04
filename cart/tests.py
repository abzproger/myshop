from django.test import TestCase, Client
from django.urls import reverse
from catalog.models import Category, Product, ProductVariant


class CartViewTest(TestCase):
    """Тесты корзины."""

    def setUp(self):
        self.client = Client()
        cat = Category.objects.create(name='Тест', slug='test')
        product = Product.objects.create(
            category=cat, name='Товар', slug='product',
            price=100, stock=10, is_active=True
        )
        self.variant = ProductVariant.objects.create(
            product=product, name='Вариант', sku='SKU-1',
            stock=5, is_active=True
        )

    def test_cart_detail_page_loads(self):
        response = self.client.get(reverse('cart:detail'))
        self.assertEqual(response.status_code, 200)
