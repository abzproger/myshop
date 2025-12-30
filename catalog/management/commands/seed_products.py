import random

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.crypto import get_random_string
from django.utils.text import slugify

from catalog.models import Category, Product, ProductVariant


class Command(BaseCommand):
    help = "Создаёт тестовые категории/товары/варианты для разработки."

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=12,
            help="Сколько товаров создать (по умолчанию 12).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        count = options["count"]
        if count < 1:
            self.stdout.write(self.style.WARNING("count < 1 — нечего создавать."))
            return

        # 1) Категории (если уже есть — используем существующие)
        categories = list(Category.objects.all()[:10])
        if not categories:
            base_categories = [
                "Диваны",
                "Кровати",
                "Столы",
            ]
            for name in base_categories:
                slug = slugify(name)
                if Category.objects.filter(slug=slug).exists():
                    slug = f"{slug}-{get_random_string(6).lower()}"
                categories.append(Category.objects.create(name=name, slug=slug))

        # 2) Товары + 1 вариант на товар (для каталога важны именно варианты)
        adjectives = ["Современный", "Классический", "Компактный", "Угловой", "Модульный", "Дизайнерский"]
        nouns = ["диван", "стол", "кресло", "шкаф", "комод", "кровать", "тумба", "стеллаж"]
        materials = ["бук", "дуб", "сосна", "металл", "ткань", "экокожа"]

        created_products = 0
        created_variants = 0

        for i in range(count):
            cat = random.choice(categories)

            name = f"{random.choice(adjectives)} {random.choice(nouns)} ({random.choice(materials)})"
            # Делаем slug уникальным
            slug_base = slugify(name) or f"product-{get_random_string(6).lower()}"
            slug = f"{slug_base}-{get_random_string(6).lower()}"

            price = random.randrange(4990, 89990, 500)
            stock = random.randrange(0, 50)

            product = Product.objects.create(
                category=cat,
                name=name,
                slug=slug,
                price=price,
                description="Тестовый товар для проверки каталога, пагинации и карточки товара.",
                stock=stock,
                is_active=True,
            )
            created_products += 1

            # SKU должен быть уникальным
            sku = f"TEST-{get_random_string(8).upper()}"
            while ProductVariant.objects.filter(sku=sku).exists():
                sku = f"TEST-{get_random_string(8).upper()}"

            variant = ProductVariant.objects.create(
                product=product,
                name=f"Вариант {i + 1}",
                size=random.choice(["S", "M", "L", "XL"]),
                color=random.choice(["белый", "чёрный", "серый", "бежевый", "коричневый"]),
                price=None,  # пусть берётся price товара
                stock=stock,
                sku=sku,
                is_active=True,
            )
            created_variants += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Готово. Создано товаров: {created_products}, вариантов: {created_variants}."
            )
        )


