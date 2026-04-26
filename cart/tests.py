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

    def test_cart_add_invalid_quantity_falls_back_to_one(self):
        response = self.client.post(
            reverse('cart:add', args=[self.variant.id]),
            {"quantity": "abc"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session["cart"][str(self.variant.id)]["quantity"], 1)

    def test_cart_add_rejects_out_of_stock_variant(self):
        self.variant.stock = 0
        self.variant.save(update_fields=["stock"])

        response = self.client.post(reverse('cart:add', args=[self.variant.id]), {"quantity": 1})

        self.assertEqual(response.status_code, 302)
        self.assertNotIn(str(self.variant.id), self.client.session.get("cart", {}))

    def test_cart_detail_removes_stale_items_from_session(self):
        session = self.client.session
        session["cart"] = {"999999": {"quantity": 2, "price": "100.00"}}
        session.save()

        response = self.client.get(reverse("cart:detail"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ваша корзина пуста")
        self.assertEqual(self.client.session.get("cart", {}), {})
