from rest_framework.routers import DefaultRouter

from .api_views import CategoryViewSet, ProductViewSet, ProductVariantViewSet

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("products", ProductViewSet, basename="product")
router.register("variants", ProductVariantViewSet, basename="variant")

urlpatterns = router.urls



