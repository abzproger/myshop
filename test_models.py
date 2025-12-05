#!/usr/bin/env python
"""Тестовый скрипт для проверки моделей каталога"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop.settings')
django.setup()

from catalog.models import Category, Product, ProductVariant, ProductImage, Attribute, AttributeValue

print("=" * 60)
print("ТЕСТИРОВАНИЕ МОДЕЛЕЙ КАТАЛОГА")
print("=" * 60)

# 1. Создание категорий
print("\n1. Создание категорий...")
cat_furniture = Category.objects.create(
    name="Мебель",
    slug="furniture",
    description="Категория мебели"
)
print(f"✓ Создана категория: {cat_furniture}")

cat_chairs = Category.objects.create(
    name="Стулья",
    slug="chairs",
    parent=cat_furniture,
    description="Стулья различных типов"
)
print(f"✓ Создана подкатегория: {cat_chairs}")

# 2. Создание товара
print("\n2. Создание товара...")
product = Product.objects.create(
    category=cat_chairs,
    name="Офисный стул",
    slug="office-chair",
    price=5000.00,
    description="Удобный офисный стул с регулируемой высотой",
    stock=10,
    is_active=True
)
print(f"✓ Создан товар: {product}")

# 3. Создание вариантов товара
print("\n3. Создание вариантов товара...")
variant1 = ProductVariant.objects.create(
    product=product,
    name="Черный",
    size="M",
    color="Черный",
    price=5000.00,
    stock=5,
    sku="CHAIR-BLACK-M",
    is_active=True
)
print(f"✓ Создан вариант: {variant1}")

variant2 = ProductVariant.objects.create(
    product=product,
    name="Серый",
    size="L",
    color="Серый",
    price=5500.00,
    stock=3,
    sku="CHAIR-GRAY-L",
    is_active=True
)
print(f"✓ Создан вариант: {variant2}")

# 4. Создание характеристик
print("\n4. Создание характеристик...")
attr_material = Attribute.objects.create(name="Материал")
attr_weight = Attribute.objects.create(name="Вес")
print(f"✓ Созданы характеристики: {attr_material}, {attr_weight}")

# 5. Создание значений характеристик
print("\n5. Создание значений характеристик...")
attr_val1 = AttributeValue.objects.create(
    variant=variant1,
    attribute=attr_material,
    value="Пластик, металл"
)
print(f"✓ Создано значение: {attr_val1}")

attr_val2 = AttributeValue.objects.create(
    variant=variant1,
    attribute=attr_weight,
    value="8 кг"
)
print(f"✓ Создано значение: {attr_val2}")

# 6. Проверка связей
print("\n6. Проверка связей...")
print(f"✓ Категория '{cat_chairs}' имеет {cat_chairs.products.count()} товар(ов)")
print(f"✓ Товар '{product}' имеет {product.variants.count()} вариант(ов)")
print(f"✓ Вариант '{variant1}' имеет {variant1.attributes.count()} характеристик(и)")
print(f"✓ Вариант '{variant1}' имеет {variant1.images.count()} изображений")

# 7. Проверка иерархии категорий
print("\n7. Проверка иерархии категорий...")
print(f"✓ Категория '{cat_chairs}' имеет родителя: {cat_chairs.parent}")
print(f"✓ Категория '{cat_furniture}' имеет {cat_furniture.children.count()} подкатегорий")

# 8. Вывод всех созданных объектов
print("\n8. Сводка созданных объектов:")
print(f"   Категории: {Category.objects.count()}")
print(f"   Товары: {Product.objects.count()}")
print(f"   Варианты: {ProductVariant.objects.count()}")
print(f"   Характеристики: {Attribute.objects.count()}")
print(f"   Значения характеристик: {AttributeValue.objects.count()}")

print("\n" + "=" * 60)
print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
print("=" * 60)

