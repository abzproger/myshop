from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from cart.cart import Cart
from .models import Order
from .forms import CheckoutContactForm, CheckoutAddressForm


CHECKOUT_CONTACT_KEY = "checkout_contact"
CHECKOUT_ADDRESS_KEY = "checkout_address"


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
        .only("id", "created", "status", "paid", "address", "user", "email")
    )
    return render(request, "orders/history.html", {"orders": orders})


@login_required
def order_detail(request, order_id: int):
    """Детали заказа. Доступны только владельцу."""
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
        ),
        id=order_id,
    )

    # Проверка прав: владелец заказа или "старый" заказ по тому же email (если user был NULL).
    if order.user_id == user.id:
        pass
    elif order.user_id is None and user.email and (order.email or "").lower() == user.email.lower():
        # Привяжем заказ к аккаунту, чтобы история начала отображаться корректно.
        order.user = user
        order.save(update_fields=["user"])
    else:
        raise Http404

    return render(request, "orders/detail.html", {"order": order})


@login_required
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


@login_required
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


@login_required
def checkout_confirm(request):
    """Шаг 3: подтверждение заказа.

    Здесь пока только отображаем данные и «подтверждаем» без сохранения в БД.
    В будущем сюда можно добавить создание моделей заказа и оплату.
    """
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

    if request.method == "POST":
        # Собираем все необходимые данные
        from orders.models import Order, OrderItem
        from django.db import transaction
        contact_data = request.session.get(CHECKOUT_CONTACT_KEY)
        address_data = request.session.get(CHECKOUT_ADDRESS_KEY)

        # Проверка, что пользователю есть что сохранить
        if not contact_data or not address_data or cart.is_empty():
            messages.error(request, "Не хватает контактных данных, адреса или корзина пуста.")
            return redirect("orders:checkout_contact")
        try:
            with transaction.atomic():
                # Имя разделяем на first_name и last_name (если возможно)
                full_name = contact_data.get("full_name", "")
                parts = full_name.strip().split(" ", 1)
                first_name = parts[0]
                last_name = parts[1] if len(parts) > 1 else ""
                order = Order.objects.create(
                    user=request.user,
                    first_name=first_name,
                    last_name=last_name,
                    email=contact_data.get("email", ""),
                    phone=contact_data.get("phone", ""),
                    address=(address_data.get("city", "") + ", " + address_data.get("address_line", "")).strip(", "),
                    comment=address_data.get("comment", ""),
                )
                # Для каждого товара в корзине создаём позицию заказа
                for cart_item in cart:
                    OrderItem.objects.create(
                        order=order,
                        product=cart_item["variant"].product,
                        variant=cart_item["variant"],
                        price=cart_item["price"],
                        quantity=cart_item["quantity"],
                    )
        except Exception as e:
            messages.error(request, f"Ошибка оформления заказа: {e!s}")
            return redirect("cart:detail")
        cart.clear()
        for key in (CHECKOUT_CONTACT_KEY, CHECKOUT_ADDRESS_KEY):
            if key in request.session:
                del request.session[key]
        request.session.modified = True

        messages.success(request, "Ваш заказ подтверждён! В ближайшее время мы с вами свяжемся.")
        return redirect("orders:history")

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
