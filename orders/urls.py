from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    # Удобный алиас: /orders/ -> история заказов
    path("", views.order_history, name="index"),
    path("history/", views.order_history, name="history"),
    path("history/<int:order_id>/", views.order_detail, name="detail"),
    path("checkout/contact/", views.checkout_contact, name="checkout_contact"),
    path("checkout/address/", views.checkout_address, name="checkout_address"),
    path("checkout/confirm/", views.checkout_confirm, name="checkout_confirm"),
]