from decimal import Decimal
from django.conf import settings
from catalog.models import ProductVariant

CART_MAX_QUANTITY_PER_ITEM = 20


class Cart:
    """
    Корзина на основе сессий.

    В сессии хранится словарь вида:
    {
        '<variant_id>': {
            'quantity': <int>,
            'price': '<str decimal>',
        },
        ...
    }
    """

    def __init__(self, request):
        self.session = request.session
        cart_id = getattr(settings, "CART_SESSION_ID", "cart")
        self.cart_id = cart_id
        cart = self.session.get(cart_id)
        if cart is None:
            cart = self.session[cart_id] = {}
        self._cart = cart

    def add(self, variant: ProductVariant, quantity=1, override_quantity=False):
        variant_id = str(variant.id)
        max_qty = getattr(settings, "CART_MAX_QUANTITY_PER_ITEM", CART_MAX_QUANTITY_PER_ITEM)
        quantity = max(1, min(int(quantity), max_qty))

        if variant_id not in self._cart:
            # Фиксируем цену на момент добавления (без скидок, скидки можно считать при отображении)
            self._cart[variant_id] = {
                "quantity": 0,
                "price": str(variant.get_price_with_discount()),
            }
        if override_quantity:
            self._cart[variant_id]["quantity"] = quantity
        else:
            new_qty = self._cart[variant_id]["quantity"] + quantity
            self._cart[variant_id]["quantity"] = min(new_qty, max_qty)
        self.save()

    def remove(self, variant: ProductVariant):
        variant_id = str(variant.id)
        if variant_id in self._cart:
            del self._cart[variant_id]
            self.save()

    def clear(self):
        self.session[self.cart_id] = {}
        self.session.modified = True

    def save(self):
        self.session[self.cart_id] = self._cart
        self.session.modified = True

    def __iter__(self):
        variant_ids = self._cart.keys()
        variants = ProductVariant.objects.filter(id__in=variant_ids).select_related("product")
        variants_map = {str(v.id): v for v in variants}

        for variant_id, item in self._cart.items():
            variant = variants_map.get(variant_id)
            if not variant:
                continue
            price = Decimal(item["price"])
            quantity = item["quantity"]
            total_price = price * quantity
            yield {
                "variant": variant,
                "price": price,
                "quantity": quantity,
                "total_price": total_price,
            }

    def __len__(self):
        return sum(item["quantity"] for item in self._cart.values())

    def get_total_price(self):
        total = Decimal("0.00")
        for item in self:
            total += item["total_price"]
        return total

    def is_empty(self):
        return len(self._cart) == 0

    def __contains__(self, item):
        """Позволяет писать: `if variant in cart` в шаблонах."""
        if hasattr(item, "id"):
            key = str(item.id)
        else:
            key = str(item)
        return key in self._cart

    def get_item(self, variant: ProductVariant):
        """Возвращает данные по варианту в корзине или None."""
        data = self._cart.get(str(variant.id))
        if not data:
            return None
        price = Decimal(data["price"])
        quantity = data["quantity"]
        return {
            "price": price,
            "quantity": quantity,
            "total_price": price * quantity,
        }


