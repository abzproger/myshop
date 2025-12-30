from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ("product", "variant", "price", "quantity", "line_total")
    readonly_fields = ("line_total",)
    raw_id_fields = ("product", "variant")

    @admin.display(description="Сумма")
    def line_total(self, obj: OrderItem):
        return obj.get_cost()


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "created", "status", "paid", "user", "email", "phone", "total_cost", "items_count")
    list_filter = ("status", "paid", "created")
    search_fields = ("id", "email", "phone", "first_name", "last_name", "user__username")
    ordering = ("-created",)
    date_hierarchy = "created"
    list_select_related = ("user",)
    raw_id_fields = ("user",)

    fieldsets = (
        (
            "Основное",
            {
                "fields": (
                    ("status", "paid"),
                    ("created", "updated"),
                    "user",
                )
            },
        ),
        (
            "Контакты",
            {
                "fields": (
                    ("first_name", "last_name"),
                    ("phone", "email"),
                )
            },
        ),
        ("Доставка", {"fields": ("address",)}),
        ("Комментарий", {"fields": ("comment",)}),
    )

    readonly_fields = ("created", "updated")
    inlines = (OrderItemInline,)

    @admin.display(description="Итого")
    def total_cost(self, obj: Order):
        return obj.get_total_cost()

    @admin.display(description="Позиции")
    def items_count(self, obj: Order):
        return obj.items.count()


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "product", "variant", "price", "quantity", "line_total")
    list_filter = ("order__created",)
    search_fields = ("order__id", "product__name", "variant__sku")
    raw_id_fields = ("order", "product", "variant")
    list_select_related = ("order", "product", "variant")

    @admin.display(description="Сумма")
    def line_total(self, obj: OrderItem):
        return obj.get_cost()
