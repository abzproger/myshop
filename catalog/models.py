from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.core.files.base import ContentFile
from decimal import Decimal
from io import BytesIO
import logging
import os
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

# Create your models here.
def upload_to(instance, filename):
    """Генерирует безопасный путь для загрузки файлов"""
    model_name = instance.__class__.__name__.lower()
    
    # Используем ID или slug для создания безопасного имени директории
    if hasattr(instance, 'pk') and instance.pk:
        # Если объект уже сохранен, используем ID
        dir_name = str(instance.pk)
    elif hasattr(instance, 'id') and instance.id:
        # Альтернативная проверка ID
        dir_name = str(instance.id)
    elif hasattr(instance, 'variant') and instance.variant:
        # Для ProductImage используем ID варианта товара
        if hasattr(instance.variant, 'pk') and instance.variant.pk:
            dir_name = str(instance.variant.pk)
        elif hasattr(instance.variant, 'sku') and instance.variant.sku:
            dir_name = slugify(instance.variant.sku) or 'temp'
        else:
            dir_name = 'temp'
    elif hasattr(instance, 'slug') and instance.slug:
        # Если есть slug, используем его (очищенный)
        dir_name = slugify(instance.slug) or 'temp'
    elif hasattr(instance, 'sku') and instance.sku:
        # Для вариантов товара используем SKU
        dir_name = slugify(instance.sku) or 'temp'
    elif hasattr(instance, 'product') and instance.product:
        # Для связанных объектов используем ID продукта
        if hasattr(instance.product, 'pk') and instance.product.pk:
            dir_name = str(instance.product.pk)
        elif hasattr(instance.product, 'slug') and instance.product.slug:
            dir_name = slugify(instance.product.slug) or 'temp'
        else:
            dir_name = 'temp'
    else:
        # В крайнем случае используем временное имя
        import uuid
        dir_name = str(uuid.uuid4())[:8]
    
    # Очищаем имя файла от недопустимых символов
    filename = os.path.basename(filename)
    # Сохраняем расширение файла
    name, ext = os.path.splitext(filename)
    safe_name = slugify(name) or 'file'
    safe_filename = f'{safe_name}{ext}'
    
    return f'{model_name}s/{dir_name}/{safe_filename}'

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="Слаг")
    image = models.ImageField(upload_to=upload_to, blank=True, null=True, verbose_name="Изображение")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children', db_index=True, verbose_name="Родительская категория")

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
    is_active = models.BooleanField(default=True, db_index=True, verbose_name="Активен")

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
    is_active = models.BooleanField(default=True, db_index=True, verbose_name="Активен")

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

    def save(self, *args, **kwargs):
        """
        Оптимизирует изображение при сохранении (resize + exif transpose + webp).

        Это снижает вес страниц каталога/карточки товара при большом количестве картинок.
        """
        old_name = None
        if self.pk:
            old_name = (
                ProductImage.objects.filter(pk=self.pk)
                .values_list("image", flat=True)
                .first()
            )

        if self.image and getattr(self.image, "file", None):
            try:
                # Важно: исправляем поворот по EXIF (часто на фото с телефона)
                img = Image.open(self.image)
                img = ImageOps.exif_transpose(img)

                # GIF/анимации не трогаем (чтобы не ломать)
                if (img.format or "").upper() != "GIF":
                    max_side = 1600
                    img.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)

                    has_alpha = (
                        img.mode in ("RGBA", "LA")
                        or (img.mode == "P" and "transparency" in img.info)
                    )
                    if has_alpha:
                        img = img.convert("RGBA")
                    else:
                        img = img.convert("RGB")

                    buf = BytesIO()
                    img.save(
                        buf,
                        format="WEBP",
                        quality=82,
                        method=6,
                        alpha_quality=80,
                    )
                    buf.seek(0)

                    base, _ext = os.path.splitext(self.image.name)
                    new_name = f"{base}.webp"
                    self.image.save(new_name, ContentFile(buf.getvalue()), save=False)
            except Exception as e:
                logger.warning("Не удалось оптимизировать изображение %s: %s", self.image.name, e)

        super().save(*args, **kwargs)

        # Если изменили имя файла (например jpg -> webp) — удаляем старый, чтобы не копить мусор
        if old_name and old_name != self.image.name:
            try:
                storage = self.image.storage
                if storage.exists(old_name):
                    storage.delete(old_name)
            except Exception as e:
                logger.warning("Не удалось удалить старое изображение %s: %s", old_name, e)

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
    start_date = models.DateTimeField(verbose_name="Дата начала", db_index=True)
    end_date = models.DateTimeField(verbose_name="Дата окончания", db_index=True)
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

    def clean(self):
        from django.core.exceptions import ValidationError
        super().clean()
        # В зависимости от apply_to должно быть заполнено только одно целевое поле
        if self.apply_to == self.APPLY_TO_CATEGORY:
            if not self.category_id:
                raise ValidationError({"category": "Укажите категорию для скидки на категорию."})
            if self.product_id or self.variant_id:
                raise ValidationError({"product": "Скидка на категорию не должна ссылаться на товар или вариант."})
        elif self.apply_to == self.APPLY_TO_PRODUCT:
            if not self.product_id:
                raise ValidationError({"product": "Укажите товар для скидки на товар."})
            if self.variant_id:
                raise ValidationError({"variant": "Скидка на товар не должна ссылаться на вариант."})
        elif self.apply_to == self.APPLY_TO_VARIANT:
            if not self.variant_id:
                raise ValidationError({"variant": "Укажите вариант для скидки на вариант."})


class ContactMessage(models.Model):
    """Сообщение с формы контактов"""
    SUBJECT_CHOICES = [
        ('question', 'Вопрос о товаре'),
        ('order', 'Вопрос о заказе'),
        ('delivery', 'Доставка'),
        ('warranty', 'Гарантия и возврат'),
        ('other', 'Другое'),
    ]

    name = models.CharField(max_length=200, verbose_name="Имя")
    email = models.EmailField(verbose_name="Email")
    phone = models.CharField(max_length=50, blank=True, verbose_name="Телефон")
    subject = models.CharField(
        max_length=50,
        choices=SUBJECT_CHOICES,
        blank=True,
        verbose_name="Тема обращения",
    )
    message = models.TextField(verbose_name="Сообщение")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    is_processed = models.BooleanField(default=False, verbose_name="Обработано")
    source_url = models.CharField(max_length=500, blank=True, verbose_name="Источник (URL)")

    class Meta:
        verbose_name = "Сообщение с формы контактов"
        verbose_name_plural = "Сообщения с формы контактов"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.email}) — {self.get_subject_display() or 'Без темы'}"
