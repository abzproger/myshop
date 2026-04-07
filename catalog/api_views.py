from rest_framework import viewsets, filters

from .models import Category, Product, ProductVariant
from .serializers import CategorySerializer, ProductSerializer, ProductVariantSerializer


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only API для категорий.
    """

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "slug"]


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only API для товаров с вложенными вариантами.
    """

    queryset = (
        Product.objects.filter(is_active=True)
        .select_related("category")
        .prefetch_related("variants")
    )
    serializer_class = ProductSerializer
    lookup_field = "slug"
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description", "category__name"]
    ordering_fields = ["name", "price"]
    ordering = ["name"]


class ProductVariantViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only API для вариантов товара.
    """

    queryset = (
        ProductVariant.objects.filter(is_active=True)
        .select_related("product", "product__category")
        .prefetch_related("images")
    )
    serializer_class = ProductVariantSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "sku", "product__name", "product__category__name"]
    ordering_fields = ["name", "price", "stock"]
    ordering = ["name"]
