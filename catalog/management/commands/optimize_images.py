from django.core.management.base import BaseCommand

from catalog.models import ProductImage


class Command(BaseCommand):
    help = "Оптимизирует изображения товаров (resize + webp) через Pillow для уже загруженных файлов."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Ограничить количество обрабатываемых изображений (0 = без лимита).",
        )
        parser.add_argument(
            "--only-not-webp",
            action="store_true",
            help="Обрабатывать только изображения, которые ещё не .webp",
        )

    def handle(self, *args, **options):
        limit = options["limit"] or 0
        only_not_webp = bool(options["only_not_webp"])

        qs = ProductImage.objects.all().order_by("id")
        if only_not_webp:
            qs = qs.exclude(image__iendswith=".webp")
        if limit > 0:
            qs = qs[:limit]

        total = qs.count() if limit <= 0 else len(list(qs))
        if total == 0:
            self.stdout.write(self.style.WARNING("Нет изображений для обработки."))
            return

        processed = 0
        for img in qs.iterator() if limit <= 0 else qs:
            img.save()  # внутри save() сработает оптимизация
            processed += 1
            if processed % 25 == 0:
                self.stdout.write(f"Обработано: {processed}/{total}")

        self.stdout.write(self.style.SUCCESS(f"Готово. Обработано изображений: {processed}."))


