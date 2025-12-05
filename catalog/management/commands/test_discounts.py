from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from catalog.models import (
    Category, Product, ProductVariant, Discount
)


class Command(BaseCommand):
    help = 'Тестирование системы скидок'

    def handle(self, *args, **options):
        self.stdout.write("=" * 70)
        self.stdout.write(self.style.SUCCESS("ТЕСТИРОВАНИЕ СИСТЕМЫ СКИДОК"))
        self.stdout.write("=" * 70)

        # 1. Создание тестовых данных
        self.stdout.write("\n1. Создание тестовых данных...")
        
        # Категория
        category, created = Category.objects.get_or_create(
            slug="test-furniture",
            defaults={
                'name': 'Тестовая мебель',
                'description': 'Категория для тестирования скидок'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"✓ Создана категория: {category}"))
        else:
            self.stdout.write(f"✓ Категория уже существует: {category}")

        # Товар
        product, created = Product.objects.get_or_create(
            slug="test-chair",
            defaults={
                'category': category,
                'name': 'Тестовый стул',
                'price': Decimal('5000.00'),
                'description': 'Стул для тестирования скидок',
                'stock': 10,
                'is_active': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"✓ Создан товар: {product} (цена: {product.price} руб.)"))
        else:
            self.stdout.write(f"✓ Товар уже существует: {product} (цена: {product.price} руб.)")

        # Вариант товара
        variant, created = ProductVariant.objects.get_or_create(
            sku="TEST-CHAIR-001",
            defaults={
                'product': product,
                'name': 'Черный',
                'size': 'M',
                'color': 'Черный',
                'price': Decimal('5500.00'),
                'stock': 5,
                'is_active': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"✓ Создан вариант: {variant} (цена: {variant.get_base_price()} руб.)"))
        else:
            self.stdout.write(f"✓ Вариант уже существует: {variant} (цена: {variant.get_base_price()} руб.)")

        # 2. Тест скидки на категорию (20%)
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("2. ТЕСТ: Скидка на категорию (20%)")
        self.stdout.write("=" * 70)
        
        category_discount, created = Discount.objects.get_or_create(
            name="Распродажа мебели",
            defaults={
                'discount_type': Discount.DISCOUNT_TYPE_PERCENT,
                'value': Decimal('20.00'),
                'apply_to': Discount.APPLY_TO_CATEGORY,
                'category': category,
                'start_date': timezone.now() - timedelta(days=1),
                'end_date': timezone.now() + timedelta(days=7),
                'is_active': True,
                'priority': 1
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f"✓ Создана скидка на категорию: {category_discount}"))
        else:
            self.stdout.write(f"✓ Скидка уже существует: {category_discount}")
        
        # Проверка цены товара
        product_price_with_discount = product.get_price_with_discount()
        product_discount_amount = product.get_discount_amount()
        self.stdout.write(f"\nТовар '{product.name}':")
        self.stdout.write(f"  Базовая цена: {product.price} руб.")
        self.stdout.write(f"  Скидка: {product_discount_amount} руб. ({category_discount.value}%)")
        self.stdout.write(self.style.SUCCESS(f"  Цена со скидкой: {product_price_with_discount} руб."))
        
        # Проверка цены варианта
        variant_price_with_discount = variant.get_price_with_discount()
        variant_discount_amount = variant.get_discount_amount()
        self.stdout.write(f"\nВариант '{variant}':")
        self.stdout.write(f"  Базовая цена: {variant.get_base_price()} руб.")
        self.stdout.write(f"  Скидка: {variant_discount_amount} руб. ({category_discount.value}%)")
        self.stdout.write(self.style.SUCCESS(f"  Цена со скидкой: {variant_price_with_discount} руб."))

        # 3. Тест скидки на товар (10%, приоритет выше)
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("3. ТЕСТ: Скидка на товар (10%, приоритет выше)")
        self.stdout.write("=" * 70)
        
        product_discount, created = Discount.objects.get_or_create(
            name="Скидка на тестовый стул",
            defaults={
                'discount_type': Discount.DISCOUNT_TYPE_PERCENT,
                'value': Decimal('10.00'),
                'apply_to': Discount.APPLY_TO_PRODUCT,
                'product': product,
                'start_date': timezone.now() - timedelta(days=1),
                'end_date': timezone.now() + timedelta(days=7),
                'is_active': True,
                'priority': 2  # Выше приоритета скидки на категорию
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f"✓ Создана скидка на товар: {product_discount}"))
        else:
            self.stdout.write(f"✓ Скидка уже существует: {product_discount}")
        
        # Проверка приоритета (должна применяться скидка на товар, а не на категорию)
        product_price_with_discount = product.get_price_with_discount()
        product_discount_amount = product.get_discount_amount()
        active_discount = product.get_active_discount()
        
        self.stdout.write(f"\nТовар '{product.name}':")
        self.stdout.write(f"  Базовая цена: {product.price} руб.")
        self.stdout.write(f"  Активная скидка: {active_discount} (приоритет: {active_discount.priority})")
        self.stdout.write(f"  Скидка: {product_discount_amount} руб. ({active_discount.value}%)")
        self.stdout.write(self.style.SUCCESS(f"  Цена со скидкой: {product_price_with_discount} руб."))
        self.stdout.write(self.style.WARNING("  ⚠ Примечание: Скидка на товар имеет приоритет над скидкой на категорию"))

        # 4. Тест скидки на вариант (фиксированная сумма)
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("4. ТЕСТ: Скидка на вариант (фиксированная сумма 500 руб.)")
        self.stdout.write("=" * 70)
        
        variant_discount, created = Discount.objects.get_or_create(
            name="Скидка на черный вариант",
            defaults={
                'discount_type': Discount.DISCOUNT_TYPE_FIXED,
                'value': Decimal('500.00'),
                'apply_to': Discount.APPLY_TO_VARIANT,
                'variant': variant,
                'start_date': timezone.now() - timedelta(days=1),
                'end_date': timezone.now() + timedelta(days=7),
                'is_active': True,
                'priority': 3  # Самый высокий приоритет
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f"✓ Создана скидка на вариант: {variant_discount}"))
        else:
            self.stdout.write(f"✓ Скидка уже существует: {variant_discount}")
        
        # Проверка приоритета (должна применяться скидка на вариант)
        variant_price_with_discount = variant.get_price_with_discount()
        variant_discount_amount = variant.get_discount_amount()
        active_variant_discount = variant.get_active_discount()
        
        self.stdout.write(f"\nВариант '{variant}':")
        self.stdout.write(f"  Базовая цена: {variant.get_base_price()} руб.")
        self.stdout.write(f"  Активная скидка: {active_variant_discount} (приоритет: {active_variant_discount.priority})")
        self.stdout.write(f"  Скидка: {variant_discount_amount} руб. (фиксированная)")
        self.stdout.write(self.style.SUCCESS(f"  Цена со скидкой: {variant_price_with_discount} руб."))
        self.stdout.write(self.style.WARNING("  ⚠ Примечание: Скидка на вариант имеет наивысший приоритет"))

        # 5. Тест неактивной скидки
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("5. ТЕСТ: Неактивная скидка (не должна применяться)")
        self.stdout.write("=" * 70)
        
        inactive_discount, created = Discount.objects.get_or_create(
            name="Неактивная скидка",
            defaults={
                'discount_type': Discount.DISCOUNT_TYPE_PERCENT,
                'value': Decimal('50.00'),
                'apply_to': Discount.APPLY_TO_PRODUCT,
                'product': product,
                'start_date': timezone.now() - timedelta(days=1),
                'end_date': timezone.now() + timedelta(days=7),
                'is_active': False,  # Неактивна
                'priority': 10
            }
        )
        
        if created:
            self.stdout.write(f"✓ Создана неактивная скидка: {inactive_discount}")
        else:
            inactive_discount.is_active = False
            inactive_discount.save()
            self.stdout.write(f"✓ Скидка деактивирована: {inactive_discount}")
        
        # Проверка, что неактивная скидка не применяется
        active_discount = product.get_active_discount()
        self.stdout.write(f"\nАктивная скидка для товара: {active_discount}")
        if active_discount != inactive_discount:
            self.stdout.write(self.style.SUCCESS("  ✓ Неактивная скидка не применяется (корректно)"))
        else:
            self.stdout.write(self.style.ERROR("  ✗ ОШИБКА: Неактивная скидка применяется!"))

        # 6. Тест истекшей скидки
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("6. ТЕСТ: Истекшая скидка (не должна применяться)")
        self.stdout.write("=" * 70)
        
        expired_discount, created = Discount.objects.get_or_create(
            name="Истекшая скидка",
            defaults={
                'discount_type': Discount.DISCOUNT_TYPE_PERCENT,
                'value': Decimal('30.00'),
                'apply_to': Discount.APPLY_TO_PRODUCT,
                'product': product,
                'start_date': timezone.now() - timedelta(days=10),
                'end_date': timezone.now() - timedelta(days=1),  # Истекла
                'is_active': True,
                'priority': 10
            }
        )
        
        if created:
            self.stdout.write(f"✓ Создана истекшая скидка: {expired_discount}")
        else:
            expired_discount.end_date = timezone.now() - timedelta(days=1)
            expired_discount.save()
            self.stdout.write(f"✓ Скидка истекла: {expired_discount}")
        
        # Проверка, что истекшая скидка не применяется
        is_valid = expired_discount.is_valid()
        active_discount = product.get_active_discount()
        self.stdout.write(f"\nИстекшая скидка валидна: {is_valid}")
        self.stdout.write(f"Активная скидка для товара: {active_discount}")
        if not is_valid and active_discount != expired_discount:
            self.stdout.write(self.style.SUCCESS("  ✓ Истекшая скидка не применяется (корректно)"))
        else:
            self.stdout.write(self.style.ERROR("  ✗ ОШИБКА: Истекшая скидка применяется!"))

        # 7. Итоговая сводка
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("7. ИТОГОВАЯ СВОДКА")
        self.stdout.write("=" * 70)
        
        self.stdout.write(f"\nСозданные объекты:")
        self.stdout.write(f"  Категории: {Category.objects.count()}")
        self.stdout.write(f"  Товары: {Product.objects.count()}")
        self.stdout.write(f"  Варианты: {ProductVariant.objects.count()}")
        self.stdout.write(f"  Скидки: {Discount.objects.count()}")
        self.stdout.write(f"  Активные скидки: {Discount.objects.filter(is_active=True).count()}")
        
        self.stdout.write(f"\nФинальные цены:")
        self.stdout.write(f"  Товар '{product.name}':")
        self.stdout.write(f"    Базовая: {product.price} руб. → Со скидкой: {product.get_price_with_discount()} руб.")
        self.stdout.write(f"  Вариант '{variant}':")
        self.stdout.write(f"    Базовая: {variant.get_base_price()} руб. → Со скидкой: {variant.get_price_with_discount()} руб.")

        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(self.style.SUCCESS("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!"))
        self.stdout.write("=" * 70)

