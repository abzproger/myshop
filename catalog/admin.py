from django.contrib import admin
from django.utils import timezone
from .models import (
    Category, Product, ProductVariant, 
    ProductImage, Attribute, AttributeValue, Discount
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'parent', 'image')
    list_filter = ('parent',)
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'slug', 'parent')
        }),
        ('Дополнительно', {
            'fields': ('image', 'description')
        }),
    )


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'is_main', 'alt', 'order')


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ('name', 'size', 'color', 'price', 'stock', 'sku', 'is_active')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductVariantInline]
    fieldsets = (
        ('Основная информация', {
            'fields': ('category', 'name', 'slug')
        }),
        ('Цена и остатки', {
            'fields': ('price', 'stock')
        }),
        ('Описание', {
            'fields': ('description',)
        }),
        ('Статус', {
            'fields': ('is_active',)
        }),
    )


class AttributeValueInline(admin.TabularInline):
    model = AttributeValue
    extra = 1
    fields = ('attribute', 'value')


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'product', 'size', 'color', 'price', 'stock', 'sku', 'is_active')
    list_filter = ('product', 'is_active', 'size', 'color')
    search_fields = ('product__name', 'name', 'sku', 'size', 'color')
    inlines = [ProductImageInline, AttributeValueInline]
    fieldsets = (
        ('Основная информация', {
            'fields': ('product', 'name', 'sku')
        }),
        ('Характеристики варианта', {
            'fields': ('size', 'color')
        }),
        ('Цена и остатки', {
            'fields': ('price', 'stock')
        }),
        ('Статус', {
            'fields': ('is_active',)
        }),
    )


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('variant', 'image', 'is_main', 'order')
    list_filter = ('is_main', 'variant__product')
    search_fields = ('variant__product__name', 'alt')
    ordering = ('variant', 'order')


@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(AttributeValue)
class AttributeValueAdmin(admin.ModelAdmin):
    list_display = ('variant', 'attribute', 'value')
    list_filter = ('attribute', 'variant__product')
    search_fields = ('variant__product__name', 'attribute__name', 'value')


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ('name', 'discount_type', 'value', 'apply_to', 'start_date', 'end_date', 'is_active', 'is_valid_now')
    list_filter = ('discount_type', 'apply_to', 'is_active', 'start_date', 'end_date')
    search_fields = ('name', 'description')
    date_hierarchy = 'start_date'
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'is_active', 'priority')
        }),
        ('Параметры скидки', {
            'fields': ('discount_type', 'value')
        }),
        ('Область применения', {
            'fields': ('apply_to', 'category', 'product', 'variant'),
            'description': 'Выберите тип применения и соответствующий объект'
        }),
        ('Период действия', {
            'fields': ('start_date', 'end_date')
        }),
    )

    def is_valid_now(self, obj):
        """Показывает, активна ли скидка сейчас"""
        if obj.is_valid():
            return "✓ Активна"
        now = timezone.now()
        if now < obj.start_date:
            return "⏳ Ещё не началась"
        elif now > obj.end_date:
            return "✗ Завершена"
        return "✗ Неактивна"
    is_valid_now.short_description = "Статус"

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Динамически скрываем поля в зависимости от apply_to
        if obj:
            if obj.apply_to == Discount.APPLY_TO_CATEGORY:
                form.base_fields['product'].widget.attrs['style'] = 'display:none'
                form.base_fields['variant'].widget.attrs['style'] = 'display:none'
            elif obj.apply_to == Discount.APPLY_TO_PRODUCT:
                form.base_fields['category'].widget.attrs['style'] = 'display:none'
                form.base_fields['variant'].widget.attrs['style'] = 'display:none'
            elif obj.apply_to == Discount.APPLY_TO_VARIANT:
                form.base_fields['category'].widget.attrs['style'] = 'display:none'
                form.base_fields['product'].widget.attrs['style'] = 'display:none'
        return form
