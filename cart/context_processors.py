from .cart import Cart


def cart(request):
    """
    Добавляет объект корзины и счётчик товаров во все шаблоны.
    """
    cart = Cart(request)
    return {
        "cart": cart,
        "cart_total_quantity": len(cart),
        "cart_total_price": cart.get_total_price(),
    }

