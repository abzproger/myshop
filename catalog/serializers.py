from rest_framework import serializers

from .models import Category, Product, ProductVariant, ProductImage, AttributeValue


class CategorySerializer(serializers.ModelSerializer):
    parent_id = serializers.PrimaryKeyRelatedField(
        source="parent",
        read_only=True,
    )

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "parent_id"]


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image", "is_main", "alt", "order"]


class ProductVariantSerializer(serializers.ModelSerializer):
    product_id = serializers.PrimaryKeyRelatedField(
        source="product",
        read_only=True,
    )
    base_price = serializers.SerializerMethodField()
    price_with_discount = serializers.SerializerMethodField()
    discount_amount = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = [
            "id",
            "product_id",
            "name",
            "size",
            "color",
            "price",
            "base_price",
            "price_with_discount",
            "discount_amount",
            "stock",
            "sku",
            "is_active",
        ]

    def get_base_price(self, obj: ProductVariant):
        return obj.get_base_price()

    def get_price_with_discount(self, obj: ProductVariant):
        return obj.get_price_with_discount()

    def get_discount_amount(self, obj: ProductVariant):
        return obj.get_discount_amount()


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "price",
            "stock",
            "is_active",
            "category",
            "variants",
        ]





