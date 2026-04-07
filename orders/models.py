import secrets
from decimal import Decimal

from django.conf import settings
from django.db import models

from catalog.models import Product, ProductVariant


def generate_guest_token():
    """Токен для доступа гостя к заказу по ссылке."""
    return secrets.token_urlsafe(32)


class Order(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='orders', on_delete=models.SET_NULL, blank=True, null=True, verbose_name='Пользователь'
    )
    guest_access_token = models.CharField(
        max_length=64, unique=True, null=True, blank=True,
        verbose_name='Токен доступа (гостевой заказ)',
        help_text='Ссылка с этим токеном позволяет гостю просматривать заказ без входа.',
    )
    first_name = models.CharField(max_length=100, verbose_name='Имя')
    last_name = models.CharField(max_length=100, verbose_name='Фамилия', blank=True)
    phone = models.CharField(max_length=30, verbose_name='Телефон')
    email = models.EmailField(verbose_name='Email')
    address = models.CharField(max_length=255, verbose_name='Адрес доставки')
    created = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Создан')
    updated = models.DateTimeField(auto_now=True, verbose_name='Обновлён')
    paid = models.BooleanField(default=False, verbose_name='Оплачен')
    comment = models.TextField(verbose_name='Комментарий', blank=True, null=True)
    status = models.CharField(
        max_length=20, 
        choices=[
            ('pending', 'Ожидает обработки'),
            ('processing', 'В обработке'),
            ('shipped', 'Отправлен'),
            ('delivered', 'Доставлен'),
            ('cancelled', 'Отменён'),
        ],
        default='pending',
        verbose_name='Статус'
    )

    class Meta:
        ordering = ['-created']
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return f"Заказ #{self.id} от {self.first_name} {self.last_name or ''}".strip()

    def get_total_cost(self):
        # Защита от "битых" позиций (например, если у позиции нет цены).
        total = Decimal("0.00")
        for item in self.items.all():
            total += item.get_cost()
        return total


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE, verbose_name='Заказ')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name='Товар')
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT, verbose_name='Вариант товара', blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Количество')

    class Meta:
        verbose_name = 'Позиция заказа'
        verbose_name_plural = 'Позиции заказа'

    def __str__(self):
        return f"{self.product} x{self.quantity}"

    def get_cost(self):
        # В идеале price всегда не NULL (DecimalField), но на практике в базе
        # могут встретиться старые/битые данные. Не валим админку — считаем 0.
        price = self.price if self.price is not None else Decimal("0.00")
        qty = self.quantity if self.quantity is not None else 0
        return price * qty
