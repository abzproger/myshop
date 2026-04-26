from django.contrib import admin, messages
from django.db.models import Count
from django.utils import timezone
from django.utils.html import format_html

from .models import (
    Attribute,
    AttributeValue,
    Category,
    ContactMessage,
    Discount,
    Product,
    ProductImage,
    ProductVariant,
)


def render_badge(text: str, tone: str = "neutral"):
    return format_html('<span class="admin-badge admin-badge--{}">{}</span>', tone, text)


def render_image_preview(image_field, alt_text: str):
    if not image_field:
        return "—"
    return format_html(
        '<img src="{}" alt="{}" class="admin-thumb" />',
        image_field.url,
        alt_text,
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "products_count", "image_preview")
    list_filter = ("parent",)
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("image_preview",)
    list_per_page = 25
    fieldsets = (
        ("Основная информация", {"fields": ("name", "slug", "parent")}),
        ("Дополнительно", {"fields": ("image", "image_preview", "description")}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(products_total=Count("products"))

    @admin.display(description="Товаров", ordering="products_total")
    def products_count(self, obj):
        return obj.products_total

    @admin.display(description="Изображение")
    def image_preview(self, obj):
        if not obj:
            return "—"
        return render_image_preview(obj.image, obj.name)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0
    fields = ("preview", "image", "is_main", "alt", "order")
    readonly_fields = ("preview",)

    @admin.display(description="Превью")
    def preview(self, obj):
        if not obj or not obj.pk:
            return "—"
        return render_image_preview(obj.image, str(obj.variant))


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ("name", "size", "color", "price", "stock", "sku", "is_active")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "base_price",
        "discounted_price",
        "stock_status",
        "variants_count",
        "is_active",
    )
    list_filter = ("category", "is_active")
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductVariantInline]
    autocomplete_fields = ("category",)
    list_select_related = ("category",)
    list_per_page = 25
    actions = ("activate_products", "deactivate_products")
    readonly_fields = ("discount_summary",)
    fieldsets = (
        ("Основная информация", {"fields": ("category", "name", "slug")}),
        ("Цена и остатки", {"fields": ("price", "stock", "discount_summary")}),
        ("Описание", {"fields": ("description",)}),
        ("Статус", {"fields": ("is_active",)}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("category").annotate(
            variants_total=Count("variants", distinct=True)
        )

    @admin.display(description="Цена", ordering="price")
    def base_price(self, obj):
        return f"{obj.price:.0f} ₽"

    @admin.display(description="Цена со скидкой")
    def discounted_price(self, obj):
        final_price = obj.get_price_with_discount()
        if final_price < obj.price:
            return format_html(
                '<div><s>{}</s><br><strong>{}</strong></div>',
                f"{obj.price:.0f} ₽",
                f"{final_price:.0f} ₽",
            )
        return f"{final_price:.0f} ₽"

    @admin.display(description="Остаток", ordering="stock")
    def stock_status(self, obj):
        if obj.stock == 0:
            return render_badge("Нет в наличии", "danger")
        if obj.stock < 5:
            return render_badge(f"Мало: {obj.stock}", "warning")
        return render_badge(f"В наличии: {obj.stock}", "success")

    @admin.display(description="Вариантов", ordering="variants_total")
    def variants_count(self, obj):
        return obj.variants_total

    @admin.display(description="Скидка")
    def discount_summary(self, obj):
        if not obj:
            return render_badge("Сохраните товар, чтобы увидеть скидку", "neutral")
        discount = obj.get_active_discount()
        if not discount:
            return render_badge("Нет активной скидки", "neutral")
        return format_html(
            "{} {}",
            render_badge("Активна", "success"),
            discount.name,
        )

    @admin.action(description="Активировать выбранные товары")
    def activate_products(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Активировано товаров: {updated}", level=messages.SUCCESS)

    @admin.action(description="Деактивировать выбранные товары")
    def deactivate_products(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Деактивировано товаров: {updated}", level=messages.WARNING)


class AttributeValueInline(admin.TabularInline):
    model = AttributeValue
    extra = 1
    fields = ("attribute", "value")
    autocomplete_fields = ("attribute",)


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = (
        "preview",
        "__str__",
        "sku",
        "display_price",
        "stock_status",
        "is_active",
    )
    list_filter = ("is_active", "product__category", "size", "color")
    search_fields = ("product__name", "name", "sku", "size", "color")
    inlines = [ProductImageInline, AttributeValueInline]
    autocomplete_fields = ("product",)
    list_select_related = ("product", "product__category")
    list_per_page = 25
    actions = ("activate_variants", "deactivate_variants")
    readonly_fields = ("preview",)
    fieldsets = (
        ("Основная информация", {"fields": ("product", "name", "sku", "preview")}),
        ("Характеристики варианта", {"fields": ("size", "color")}),
        ("Цена и остатки", {"fields": ("price", "stock")}),
        ("Статус", {"fields": ("is_active",)}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("product", "product__category").prefetch_related("images")

    def _get_main_image(self, obj):
        return next((image for image in obj.images.all() if image.is_main), None) or next(
            iter(obj.images.all()),
            None,
        )

    @admin.display(description="Фото")
    def preview(self, obj):
        if not obj:
            return "—"
        image = self._get_main_image(obj)
        if not image:
            return render_badge("Без фото", "neutral")
        return render_image_preview(image.image, str(obj))

    @admin.display(description="Цена")
    def display_price(self, obj):
        base_price = obj.get_base_price()
        final_price = obj.get_price_with_discount()
        if final_price < base_price:
            return format_html(
                '<div><s>{}</s><br><strong>{}</strong></div>',
                f"{base_price:.0f} ₽",
                f"{final_price:.0f} ₽",
            )
        return f"{final_price:.0f} ₽"

    @admin.display(description="Остаток", ordering="stock")
    def stock_status(self, obj):
        if obj.stock == 0:
            return render_badge("Нет", "danger")
        if obj.stock < 3:
            return render_badge(f"Мало: {obj.stock}", "warning")
        return render_badge(f"{obj.stock} шт.", "success")

    @admin.action(description="Активировать выбранные варианты")
    def activate_variants(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Активировано вариантов: {updated}", level=messages.SUCCESS)

    @admin.action(description="Деактивировать выбранные варианты")
    def deactivate_variants(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Деактивировано вариантов: {updated}", level=messages.WARNING)


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("preview", "variant", "is_main", "order")
    list_filter = ("is_main", "variant__product")
    search_fields = ("variant__product__name", "alt")
    ordering = ("variant", "order")
    autocomplete_fields = ("variant",)
    readonly_fields = ("preview",)
    list_select_related = ("variant", "variant__product")

    @admin.display(description="Превью")
    def preview(self, obj):
        if not obj:
            return "—"
        return render_image_preview(obj.image, str(obj.variant))


@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(AttributeValue)
class AttributeValueAdmin(admin.ModelAdmin):
    list_display = ("variant", "attribute", "value")
    list_filter = ("attribute", "variant__product")
    search_fields = ("variant__product__name", "attribute__name", "value")
    autocomplete_fields = ("variant", "attribute")
    list_select_related = ("variant", "variant__product", "attribute")


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "discount_type",
        "value",
        "apply_to",
        "target_object",
        "is_active",
        "is_valid_now",
        "priority",
    )
    list_filter = ("discount_type", "apply_to", "is_active", "start_date", "end_date")
    search_fields = ("name", "description")
    date_hierarchy = "start_date"
    autocomplete_fields = ("category", "product", "variant")
    list_per_page = 25
    actions = ("activate_discounts", "deactivate_discounts")
    fieldsets = (
        ("Основная информация", {"fields": ("name", "description", "is_active", "priority")}),
        ("Параметры скидки", {"fields": ("discount_type", "value")}),
        (
            "Область применения",
            {
                "fields": ("apply_to", "category", "product", "variant"),
                "description": "Выберите тип применения и соответствующий объект",
            },
        ),
        ("Период действия", {"fields": ("start_date", "end_date")}),
    )

    @admin.display(description="Объект")
    def target_object(self, obj):
        return obj.category or obj.product or obj.variant or "—"

    def is_valid_now(self, obj):
        if obj.is_valid():
            return render_badge("Активна", "success")
        now = timezone.now()
        if now < obj.start_date:
            return render_badge("Еще не началась", "warning")
        if now > obj.end_date:
            return render_badge("Завершена", "danger")
        return render_badge("Неактивна", "neutral")

    is_valid_now.short_description = "Статус"

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj:
            if obj.apply_to == Discount.APPLY_TO_CATEGORY:
                form.base_fields["product"].widget.attrs["style"] = "display:none"
                form.base_fields["variant"].widget.attrs["style"] = "display:none"
            elif obj.apply_to == Discount.APPLY_TO_PRODUCT:
                form.base_fields["category"].widget.attrs["style"] = "display:none"
                form.base_fields["variant"].widget.attrs["style"] = "display:none"
            elif obj.apply_to == Discount.APPLY_TO_VARIANT:
                form.base_fields["category"].widget.attrs["style"] = "display:none"
                form.base_fields["product"].widget.attrs["style"] = "display:none"
        return form

    @admin.action(description="Активировать выбранные скидки")
    def activate_discounts(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Активировано скидок: {updated}", level=messages.SUCCESS)

    @admin.action(description="Деактивировать выбранные скидки")
    def deactivate_discounts(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Деактивировано скидок: {updated}", level=messages.WARNING)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "subject",
        "created_at",
        "processed_status",
        "contact_link",
        "message_short",
    )
    list_filter = ("is_processed", "subject", "created_at")
    search_fields = ("name", "email", "phone", "message")
    readonly_fields = ("created_at", "source_url")
    list_per_page = 25
    actions = ("mark_processed", "mark_unprocessed")
    fieldsets = (
        ("Клиент", {"fields": (("name", "email"), "phone")}),
        ("Обращение", {"fields": ("subject", "message")}),
        ("Служебное", {"fields": ("is_processed", "created_at", "source_url")}),
    )

    @admin.display(description="Статус", ordering="is_processed")
    def processed_status(self, obj):
        return render_badge("Обработано", "success") if obj.is_processed else render_badge("Новое", "warning")

    @admin.display(description="Контакт")
    def contact_link(self, obj):
        return format_html('<a href="mailto:{}">{}</a>', obj.email, obj.email)

    @admin.display(description="Сообщение")
    def message_short(self, obj):
        if len(obj.message) <= 80:
            return obj.message
        return f"{obj.message[:77]}..."

    @admin.action(description="Пометить выбранные обращения как обработанные")
    def mark_processed(self, request, queryset):
        updated = queryset.update(is_processed=True)
        self.message_user(request, f"Обработано обращений: {updated}", level=messages.SUCCESS)

    @admin.action(description="Вернуть выбранные обращения в новые")
    def mark_unprocessed(self, request, queryset):
        updated = queryset.update(is_processed=False)
        self.message_user(request, f"Возвращено в новые: {updated}", level=messages.WARNING)
