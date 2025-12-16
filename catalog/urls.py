from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.index, name='index'),
    path('catalog/', views.catalog, name='catalog'),
    path('catalog/<slug:category_slug>/', views.catalog, name='catalog_by_category'),
    path('product/<slug:product_slug>/', views.product_detail, name='product_detail'),
    path('about/', views.about, name='about'),
    path('privacy/', views.privacy, name='privacy'),
    path('contacts/', views.contacts, name='contacts'),
]

