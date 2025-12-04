from django.db import models

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
    image = models.ImageField(upload_to=upload_to, blank=True, null=True, verbose_name="Изображение")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    stock = models.PositiveIntegerField(default=0, verbose_name="Остаток на складе")
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

    def __str__(self):
        return self.name

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants', verbose_name="Товар")
    name = models.CharField(max_length=150, verbose_name="Название варианта")
    size = models.CharField(max_length=50, blank=True, null=True, verbose_name="Размер")
    color = models.CharField(max_length=50, blank=True, null=True, verbose_name="Цвет")
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Цена варианта")
    stock = models.PositiveIntegerField(default=0, verbose_name="Остаток варианта")
    sku = models.CharField(max_length=50, unique=True, verbose_name="Артикул (SKU)")
    image = models.ImageField(upload_to=upload_to, blank=True, null=True, verbose_name="Картинка варианта")
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

