import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from catalog.models import ProductVariant
from cart.cart import Cart
from .models import Order, OrderItem, generate_guest_token
from .forms import CheckoutContactForm, CheckoutAddressForm, OrderCancelForm


CHECKOUT_CONTACT_KEY = "checkout_contact"
CHECKOUT_ADDRESS_KEY = "checkout_address"


def _build_order_address(address_data):
    delivery_method = address_data.get("delivery_method")
    parts = []

    if delivery_method == "pickup":
        parts.append("Самовывоз")
    elif delivery_method == "courier":
        parts.append("Доставка курьером")

    for value in (
        address_data.get("postal_code", ""),
        address_data.get("city", ""),
        address_data.get("address_line", ""),
    ):
        value = value.strip()
        if value:
            parts.append(value)

    return ", ".join(parts)


@login_required
def order_history(request):
    """История заказов текущего пользователя."""
    user = request.user

    # Если по каким-то причинам старые заказы создавались без user (NULL),
    # но email совпадает — привязываем их к аккаунту и показываем в истории.
    if user.email:
        Order.objects.filter(user__isnull=True, email__iexact=user.email).update(user=user)

    orders = (
        Order.objects.filter(
            Q(user=user)
            | (Q(user__isnull=True) & Q(email__iexact=user.email))  # на всякий случай, если update выше не сработал
        )
        .prefetch_related("items", "items__product", "items__variant")
        .only("id", "created", "status", "paid", "address", "user", "email", "cancel_reason")
    )
    return render(request, "orders/history.html", {"orders": orders})


@login_required
def order_detail(request, order_id: int):
    """Детали заказа. Доступны владельцу. Гость смотрит заказ по ссылке (orders:guest_detail)."""
    user = request.user
    order = get_object_or_404(
        Order.objects.prefetch_related("items", "items__product", "items__variant").only(
            "id",
            "created",
            "updated",
            "status",
            "paid",
            "address",
            "user",
            "first_name",
            "last_name",
            "phone",
            "email",
            "comment",
            "cancel_reason",
        ),
        id=order_id,
    )

    # Гостевой заказ — только через guest_detail с токеном
    if order.user_id is None:
        raise Http404

    if order.user_id != user.id:
        raise Http404
    # Привязка "старого" заказа по email к аккаунту
    if user.email and (order.email or "").lower() == user.email.lower():
        order.user = user
        order.save(update_fields=["user"])

    return render(
        request,
        "orders/detail.html",
        {
            "order": order,
            "is_guest": False,
            "cancel_form": OrderCancelForm(),
        },
    )


def order_guest_detail(request, order_id: int, token: str):
    """Детали заказа для гостя по секретной ссылке (без входа)."""
    order = get_object_or_404(
        Order.objects.prefetch_related("items", "items__product", "items__variant").only(
            "id",
            "created",
            "updated",
            "status",
            "paid",
            "address",
            "user",
            "first_name",
            "last_name",
            "phone",
            "email",
            "comment",
            "guest_access_token",
            "cancel_reason",
        ),
        id=order_id,
        guest_access_token=token,
    )
    return render(request, "orders/detail.html", {"order": order, "is_guest": True})


@login_required
def order_cancel(request, order_id: int):
    if request.method != "POST":
        return redirect("orders:detail", order_id=order_id)

    order = get_object_or_404(Order, id=order_id, user=request.user)

    if not order.can_be_cancelled:
        messages.error(request, "Отменить заказ уже нельзя: он уже отправлен или завершён.")
        return redirect("orders:detail", order_id=order.id)

    form = OrderCancelForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Выберите причину отмены заказа.")
        return render(
            request,
            "orders/detail.html",
            {
                "order": order,
                "is_guest": False,
                "cancel_form": form,
            },
        )

    order.status = "cancelled"
    order.cancel_reason = form.cleaned_data["reason"]
    order.save(update_fields=["status", "cancel_reason", "updated"])
    messages.success(request, "Заказ успешно отменён.")
    return redirect("orders:detail", order_id=order.id)


def checkout_contact(request):
    """Шаг 1: контактные данные."""
    cart = Cart(request)
    if cart.is_empty():
        messages.error(request, "Ваша корзина пуста. Добавьте товары перед оформлением заказа.")
        return redirect("cart:detail")

    initial = {}
    # Предзаполнение из профиля пользователя
    user = request.user
    if user.is_authenticated:
        if user.get_full_name():
            initial["full_name"] = user.get_full_name()
        if user.email:
            initial["email"] = user.email

    # Если уже есть данные в сессии — используем их
    session_data = request.session.get(CHECKOUT_CONTACT_KEY)
    if session_data:
        initial.update(session_data)

    if request.method == "POST":
        form = CheckoutContactForm(request.POST)
        if form.is_valid():
            request.session[CHECKOUT_CONTACT_KEY] = form.cleaned_data
            request.session.modified = True
            return redirect("orders:checkout_address")
    else:
        form = CheckoutContactForm(initial=initial)

    return render(
        request,
        "orders/checkout_contact.html",
        {
            "form": form,
            "cart": cart,
            "step": 1,
            "total_steps": 3,
        },
    )


def checkout_address(request):
    """Шаг 2: адрес доставки."""
    cart = Cart(request)
    if cart.is_empty():
        messages.error(request, "Ваша корзина пуста. Добавьте товары перед оформлением заказа.")
        return redirect("cart:detail")

    # Нельзя перейти к адресу, если не заполнен шаг 1
    if CHECKOUT_CONTACT_KEY not in request.session:
        return redirect("orders:checkout_contact")

    initial = request.session.get(CHECKOUT_ADDRESS_KEY, {})

    if request.method == "POST":
        form = CheckoutAddressForm(request.POST)
        if form.is_valid():
            request.session[CHECKOUT_ADDRESS_KEY] = form.cleaned_data
            request.session.modified = True
            return redirect("orders:checkout_confirm")
    else:
        form = CheckoutAddressForm(initial=initial)

    return render(
        request,
        "orders/checkout_address.html",
        {
            "form": form,
            "cart": cart,
            "step": 2,
            "total_steps": 3,
        },
    )


def checkout_confirm(request):
    """Шаг 3: просмотр данных и подтверждение заказа (создание записи в БД)."""
    cart = Cart(request)
    if cart.is_empty():
        messages.error(request, "Ваша корзина пуста. Добавьте товары перед оформлением заказа.")
        return redirect("cart:detail")

    contact_data = request.session.get(CHECKOUT_CONTACT_KEY)
    address_data = request.session.get(CHECKOUT_ADDRESS_KEY)

    if not contact_data:
        return redirect("orders:checkout_contact")
    if not address_data:
        return redirect("orders:checkout_address")

    cart_items = list(cart)
    if not cart_items:
        messages.error(request, "Некоторые товары в корзине больше недоступны. Проверьте состав заказа.")
        return redirect("cart:detail")

    if request.method == "POST":
        contact_data = request.session.get(CHECKOUT_CONTACT_KEY)
        address_data = request.session.get(CHECKOUT_ADDRESS_KEY)
        cart_items = list(cart)

        # Проверка, что пользователю есть что сохранить
        if not contact_data or not address_data or not cart_items:
            messages.error(request, "Не хватает контактных данных, адреса или корзина пуста.")
            return redirect("orders:checkout_contact")
        try:
            with transaction.atomic():
                variant_ids = [item["variant"].id for item in cart_items]
                variants = ProductVariant.objects.select_for_update().select_related("product").filter(
                    id__in=variant_ids,
                    is_active=True,
                    product__is_active=True,
                )
                variants_map = {variant.id: variant for variant in variants}
                unavailable_items = []

                for cart_item in cart_items:
                    variant = variants_map.get(cart_item["variant"].id)
                    if not variant:
                        unavailable_items.append("Один из товаров в корзине больше недоступен.")
                        continue
                    if variant.stock < cart_item["quantity"]:
                        unavailable_items.append(
                            f'Недостаточно остатка для "{variant}". Доступно: {variant.stock} шт.'
                        )

                if unavailable_items:
                    for message in unavailable_items:
                        messages.error(request, message)
                    return redirect("cart:detail")

                full_name = contact_data.get("full_name", "")
                parts = full_name.strip().split(" ", 1)
                first_name = parts[0]
                last_name = parts[1] if len(parts) > 1 else ""
                is_guest = not request.user.is_authenticated
                order = Order.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    guest_access_token=generate_guest_token() if is_guest else None,
                    first_name=first_name,
                    last_name=last_name,
                    email=contact_data.get("email", ""),
                    phone=contact_data.get("phone", ""),
                    address=_build_order_address(address_data),
                    comment=address_data.get("comment", ""),
                )
                for cart_item in cart_items:
                    variant = variants_map[cart_item["variant"].id]
                    OrderItem.objects.create(
                        order=order,
                        product=variant.product,
                        variant=variant,
                        price=cart_item["price"],
                        quantity=cart_item["quantity"],
                    )
        except Exception as e:
            logging.exception("Ошибка оформления заказа: %s", e)
            messages.error(request, "Ошибка оформления заказа. Пожалуйста, попробуйте позже или свяжитесь с нами.")
            return redirect("cart:detail")
        cart.clear()
        for key in (CHECKOUT_CONTACT_KEY, CHECKOUT_ADDRESS_KEY):
            if key in request.session:
                del request.session[key]
        request.session.modified = True

        messages.success(request, "Ваш заказ подтверждён! В ближайшее время мы с вами свяжемся.")
        if request.user.is_authenticated:
            return redirect("orders:detail", order_id=order.id)
        return redirect("orders:guest_detail", order_id=order.id, token=order.guest_access_token)

    return render(
        request,
        "orders/checkout_confirm.html",
        {
            "cart": cart,
            "contact": contact_data,
            "address": address_data,
            "step": 3,
            "total_steps": 3,
        },
    )
