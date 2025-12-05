from django.db import models
from django.utils import timezone
from decimal import Decimal

# Create your models here.
def upload_to(instance, filename):
    model_name = instance.__class__.__name__.lower()
    dir_name = f'{instance}'
    return f'{model_name}s/{dir_name}/{filename}'

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="Слаг")
    image = models.ImageField(upload_to=upload_to, blank=True, null=True, verbose_name="Изображение")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children', verbose_name="Родительская категория")

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        # Для читаемого представления многоуровневой структуры
        parts = [self.name]
        p = self.parent
        while p:
            parts.append(p.name)
            p = p.parent
        return ' / '.join(reversed(parts))


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name="Категория")
    name = models.CharField(max_length=200, verbose_name="Название")
    slug = models.SlugField(max_length=200, unique=True, verbose_name="Слаг")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    stock = models.PositiveIntegerField(default=0, verbose_name="Остаток на складе")
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

    def __str__(self):
        return self.name

    def get_active_discount(self):
        """Получает активную скидку для товара (приоритет: товар > категория)"""
        from django.utils import timezone
        now = timezone.now()
        
        # Сначала проверяем скидку на товар
        product_discount = self.discounts.filter(
            is_active=True,
            start_date__lte=now,
            end_date__gte=now,
            apply_to=Discount.APPLY_TO_PRODUCT
        ).order_by('-priority').first()
        
        if product_discount:
            return product_discount
        
        # Затем проверяем скидку на категорию
        category_discount = self.category.discounts.filter(
            is_active=True,
            start_date__lte=now,
            end_date__gte=now,
            apply_to=Discount.APPLY_TO_CATEGORY
        ).order_by('-priority').first()
        
        return category_discount

    def get_price_with_discount(self):
        """Возвращает цену товара с учетом скидки"""
        discount = self.get_active_discount()
        if discount:
            return discount.apply_discount(self.price)
        return self.price

    def get_discount_amount(self):
        """Возвращает сумму скидки"""
        discount = self.get_active_discount()
        if discount:
            return discount.calculate_discount(self.price)
        return Decimal('0.00')

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants', verbose_name="Товар")
    name = models.CharField(max_length=150, verbose_name="Название варианта")
    size = models.CharField(max_length=50, blank=True, null=True, verbose_name="Размер")
    color = models.CharField(max_length=50, blank=True, null=True, verbose_name="Цвет")
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Цена варианта")
    stock = models.PositiveIntegerField(default=0, verbose_name="Остаток варианта")
    sku = models.CharField(max_length=50, unique=True, verbose_name="Артикул (SKU)")
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    class Meta:
        verbose_name = "Вариант товара"
        verbose_name_plural = "Варианты товара"

    def __str__(self):
        parts = [self.product.name]
        if self.name:
            parts.append(self.name)
        if self.size:
            parts.append(self.size)
        if self.color:
            parts.append(self.color)
        return " / ".join(parts)

    def get_base_price(self):
        """Возвращает базовую цену варианта (если указана) или цену товара"""
        return self.price if self.price is not None else self.product.price

    def get_active_discount(self):
        """Получает активную скидку для варианта (приоритет: вариант > товар > категория)"""
        from django.utils import timezone
        now = timezone.now()
        
        # Сначала проверяем скидку на вариант
        variant_discount = self.discounts.filter(
            is_active=True,
            start_date__lte=now,
            end_date__gte=now,
            apply_to=Discount.APPLY_TO_VARIANT
        ).order_by('-priority').first()
        
        if variant_discount:
            return variant_discount
        
        # Затем проверяем скидку на товар
        product_discount = self.product.discounts.filter(
            is_active=True,
            start_date__lte=now,
            end_date__gte=now,
            apply_to=Discount.APPLY_TO_PRODUCT
        ).order_by('-priority').first()
        
        if product_discount:
            return product_discount
        
        # Затем проверяем скидку на категорию
        category_discount = self.product.category.discounts.filter(
            is_active=True,
            start_date__lte=now,
            end_date__gte=now,
            apply_to=Discount.APPLY_TO_CATEGORY
        ).order_by('-priority').first()
        
        return category_discount

    def get_price_with_discount(self):
        """Возвращает цену варианта с учетом скидки"""
        base_price = self.get_base_price()
        discount = self.get_active_discount()
        if discount:
            return discount.apply_discount(base_price)
        return base_price

    def get_discount_amount(self):
        """Возвращает сумму скидки для варианта"""
        base_price = self.get_base_price()
        discount = self.get_active_discount()
        if discount:
            return discount.calculate_discount(base_price)
        return Decimal('0.00')

class ProductImage(models.Model):
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='images', verbose_name="Вариант товара")
    image = models.ImageField(upload_to=upload_to, verbose_name="Изображение")
    is_main = models.BooleanField(default=False, verbose_name="Основное фото")
    alt = models.CharField(max_length=200, blank=True, verbose_name="Альтернативный текст")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок показа")

    class Meta:
        ordering = ['order']
        verbose_name = "Изображение варианта товара"
        verbose_name_plural = "Изображения вариантов товара"

    def __str__(self):
        return f"{self.variant} (Фото {self.pk})"

class Attribute(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название характеристики")

    class Meta:
        verbose_name = "Характеристика товара"
        verbose_name_plural = "Характеристики товаров"

    def __str__(self):
        return self.name

class AttributeValue(models.Model):
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name='values', verbose_name="Характеристика")
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='attributes', verbose_name="Вариант товара")
    value = models.CharField(max_length=255, verbose_name="Значение")

    class Meta:
        verbose_name = "Значение характеристики варианта товара"
        verbose_name_plural = "Значения характеристик вариантов товара"
        unique_together = (('variant', 'attribute'),)

    def __str__(self):
        return f"{self.variant}: {self.attribute.name} = {self.value}"


class Discount(models.Model):
    DISCOUNT_TYPE_PERCENT = 'percent'
    DISCOUNT_TYPE_FIXED = 'fixed'
    DISCOUNT_TYPE_CHOICES = [
        (DISCOUNT_TYPE_PERCENT, 'Процентная скидка'),
        (DISCOUNT_TYPE_FIXED, 'Фиксированная сумма'),
    ]

    APPLY_TO_CATEGORY = 'category'
    APPLY_TO_PRODUCT = 'product'
    APPLY_TO_VARIANT = 'variant'
    APPLY_TO_CHOICES = [
        (APPLY_TO_CATEGORY, 'Категория'),
        (APPLY_TO_PRODUCT, 'Товар'),
        (APPLY_TO_VARIANT, 'Вариант товара'),
    ]

    name = models.CharField(max_length=200, verbose_name="Название скидки")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    discount_type = models.CharField(
        max_length=10,
        choices=DISCOUNT_TYPE_CHOICES,
        default=DISCOUNT_TYPE_PERCENT,
        verbose_name="Тип скидки"
    )
    value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Значение скидки",
        help_text="Процент (0-100) или фиксированная сумма"
    )
    apply_to = models.CharField(
        max_length=10,
        choices=APPLY_TO_CHOICES,
        verbose_name="Применяется к"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='discounts',
        verbose_name="Категория"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='discounts',
        verbose_name="Товар"
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='discounts',
        verbose_name="Вариант товара"
    )
    start_date = models.DateTimeField(verbose_name="Дата начала")
    end_date = models.DateTimeField(verbose_name="Дата окончания")
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    priority = models.PositiveIntegerField(
        default=0,
        verbose_name="Приоритет",
        help_text="Чем выше число, тем выше приоритет (применяется первым)"
    )

    class Meta:
        verbose_name = "Скидка"
        verbose_name_plural = "Скидки"
        ordering = ['-priority', '-start_date']

    def __str__(self):
        return f"{self.name} ({self.get_discount_type_display()}: {self.value})"

    def is_valid(self):
        """Проверяет, активна ли скидка в данный момент"""
        now = timezone.now()
        return (
            self.is_active and
            self.start_date <= now <= self.end_date
        )

    def calculate_discount(self, price):
        """Рассчитывает сумму скидки для указанной цены"""
        if not self.is_valid():
            return Decimal('0.00')
        
        if self.discount_type == self.DISCOUNT_TYPE_PERCENT:
            return (price * self.value) / Decimal('100')
        else:  # DISCOUNT_TYPE_FIXED
            return min(self.value, price)  # Скидка не может быть больше цены

    def apply_discount(self, price):
        """Применяет скидку к цене и возвращает итоговую цену"""
        discount_amount = self.calculate_discount(price)
        return max(price - discount_amount, Decimal('0.00'))  # Цена не может быть отрицательной

