from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.urls import reverse
from catalog.models import ProductVariant
from .cart import Cart, CART_MAX_QUANTITY_PER_ITEM


@require_POST
def cart_add(request, variant_id):
    cart = Cart(request)
    variant = get_object_or_404(ProductVariant, id=variant_id, is_active=True, product__is_active=True)
    quantity = int(request.POST.get("quantity", 1) or 1)
    quantity = max(1, min(quantity, CART_MAX_QUANTITY_PER_ITEM))

    # Режим: перезаписать количество (для AJAX-обновления из корзины)
    override = request.POST.get("override") == "1"

    # Был ли товар уже в корзине до добавления
    was_in_cart = variant in cart

    cart.add(variant=variant, quantity=quantity, override_quantity=override)

    # Куда редиректить
    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or reverse('cart:detail')

    # Если запрос AJAX — возвращаем JSON
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        item = cart.get_item(variant)
        return JsonResponse({
            "success": True,
            "quantity": item["quantity"],
            "line_total": float(item["total_price"]),
            "cart_total_quantity": len(cart),
            "cart_total_price": float(cart.get_total_price()),
        })

    # Если товар уже был в корзине и это не override-запрос — ведём в корзину,
    # иначе остаёмся на странице
    if was_in_cart and not override:
        return redirect('cart:detail')
    return redirect(next_url)


@require_POST
def cart_remove(request, variant_id):
    cart = Cart(request)
    variant = get_object_or_404(ProductVariant, id=variant_id)
    cart.remove(variant)

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({
            "success": True,
            "removed": True,
            "cart_total_quantity": len(cart),
            "cart_total_price": float(cart.get_total_price()),
            "cart_empty": cart.is_empty(),
        })

    return redirect('cart:detail')


def cart_detail(request):
    cart = Cart(request)
    return render(request, 'cart/detail.html', {'cart': cart})
