from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from catalog.models import Category, Product, ProductVariant
from .models import Order

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
        category = Category.objects.create(name="Категория", slug="category")
        product = Product.objects.create(
            category=category,
            name="Товар",
            slug="product",
            price=100,
            stock=10,
            is_active=True,
        )
        self.variant = ProductVariant.objects.create(
            product=product,
            name="Вариант",
            sku="ORDER-SKU-1",
            stock=5,
            is_active=True,
        )

    def test_order_history_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('orders:history'), follow=True)
        self.assertRedirects(response, f"{reverse('users:login')}?next={reverse('orders:history')}")

    def _prepare_checkout_session(self, quantity=1):
        session = self.client.session
        session["cart"] = {
            str(self.variant.id): {
                "quantity": quantity,
                "price": "100.00",
            }
        }
        session["checkout_contact"] = {
            "full_name": "Иван Иванов",
            "email": "buyer@example.com",
            "phone": "+79991234567",
        }
        session["checkout_address"] = {
            "delivery_method": "courier",
            "city": "Москва",
            "address_line": "ул. Пушкина, д. 1",
            "postal_code": "101000",
            "comment": "Позвонить заранее",
        }
        session.save()

    def test_checkout_confirm_saves_delivery_details_in_address(self):
        self._prepare_checkout_session()

        response = self.client.post(reverse("orders:checkout_confirm"))

        self.assertEqual(response.status_code, 302)
        order = Order.objects.get()
        self.assertIn("Доставка курьером", order.address)
        self.assertIn("101000", order.address)
        self.assertIn("Москва", order.address)
        self.assertEqual(order.comment, "Позвонить заранее")

    def test_checkout_confirm_rejects_items_with_insufficient_stock(self):
        self.variant.stock = 1
        self.variant.save(update_fields=["stock"])
        self._prepare_checkout_session(quantity=2)

        response = self.client.post(reverse("orders:checkout_confirm"))

        self.assertRedirects(response, reverse("cart:detail"))
        self.assertEqual(Order.objects.count(), 0)

    def test_user_can_cancel_order_before_shipping(self):
        order = Order.objects.create(
            user=self.user,
            first_name="Иван",
            last_name="Иванов",
            phone="+79991234567",
            email="buyer@example.com",
            address="Москва",
            status="pending",
        )

        response = self.client.post(
            reverse("orders:cancel", args=[order.id]),
            {"reason": Order.CANCEL_REASON_CHANGED_MIND},
            follow=True,
        )

        order.refresh_from_db()
        self.assertRedirects(response, reverse("orders:detail", args=[order.id]))
        self.assertEqual(order.status, "cancelled")
        self.assertEqual(order.cancel_reason, Order.CANCEL_REASON_CHANGED_MIND)

    def test_user_cannot_cancel_order_after_shipping(self):
        order = Order.objects.create(
            user=self.user,
            first_name="Иван",
            last_name="Иванов",
            phone="+79991234567",
            email="buyer@example.com",
            address="Москва",
            status="shipped",
        )

        response = self.client.post(
            reverse("orders:cancel", args=[order.id]),
            {"reason": Order.CANCEL_REASON_CHANGED_MIND},
            follow=True,
        )

        order.refresh_from_db()
        self.assertRedirects(response, reverse("orders:detail", args=[order.id]))
        self.assertEqual(order.status, "shipped")
        self.assertEqual(order.cancel_reason, "")
