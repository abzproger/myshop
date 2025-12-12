from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from cart.cart import Cart
from .forms import CheckoutContactForm, CheckoutAddressForm


CHECKOUT_CONTACT_KEY = "checkout_contact"
CHECKOUT_ADDRESS_KEY = "checkout_address"


@login_required
def order_history(request):
    """Страница истории заказов пользователя.

    Пока заказов нет — выводится заглушка.
    В будущем сюда можно подтянуть реальные модели заказов.
    """
    # Заглушка: список заказов пустой
    orders = []
    return render(request, "orders/history.html", {"orders": orders})


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
        # Здесь можно создать заказ в БД и отправить письмо
        # Пока просто очищаем корзину и данные checkout.
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
