from django.contrib import admin
from .models import (
    Category, Product, ProductVariant, 
    ProductImage, Attribute, AttributeValue
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
