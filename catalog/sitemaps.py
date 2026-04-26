from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Category, Product


class StaticViewSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    static_routes = {
        "catalog:index": {"priority": 1.0, "changefreq": "daily"},
        "catalog:catalog": {"priority": 0.9, "changefreq": "daily"},
        "catalog:about": {"priority": 0.5, "changefreq": "monthly"},
        "catalog:contacts": {"priority": 0.5, "changefreq": "monthly"},
        "catalog:privacy": {"priority": 0.2, "changefreq": "yearly"},
    }

    def items(self):
        return list(self.static_routes)

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        return self.static_routes[item]["priority"]

    def changefreq(self, item):
        return self.static_routes[item]["changefreq"]


class CategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Category.objects.order_by("slug")

    def location(self, obj):
        return reverse("catalog:catalog_by_category", kwargs={"category_slug": obj.slug})


class ProductSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.9

    def items(self):
        return Product.objects.filter(is_active=True).order_by("slug")

    def location(self, obj):
        return reverse("catalog:product_detail", kwargs={"product_slug": obj.slug})
