from django.contrib import admin, messages
from django.utils.html import format_html

from .models import Order, OrderItem


def render_badge(text: str, tone: str = "neutral"):
    return format_html('<span class="admin-badge admin-badge--{}">{}</span>', tone, text)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ("product", "variant", "price", "quantity", "line_total")
    readonly_fields = ("line_total",)
    autocomplete_fields = ("product", "variant")
    show_change_link = True

    @admin.display(description="Сумма")
    def line_total(self, obj: OrderItem):
        return f"{obj.get_cost():.0f} ₽"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "created",
        "customer",
        "status_badge",
        "paid_badge",
        "total_cost",
        "items_count",
    )
    list_filter = ("status", "paid", "created")
    search_fields = ("id", "email", "phone", "first_name", "last_name", "user__username")
    ordering = ("-created",)
    date_hierarchy = "created"
    list_select_related = ("user",)
    autocomplete_fields = ("user",)
    list_per_page = 25
    actions = (
        "mark_processing",
        "mark_shipped",
        "mark_delivered",
        "mark_cancelled",
        "mark_paid",
    )

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
        ("Доставка", {"fields": ("address", "guest_access_token")}),
        ("Итог", {"fields": ("total_cost",)}),
        ("Комментарий", {"fields": ("comment", "cancel_reason")}),
    )

    readonly_fields = ("created", "updated", "guest_access_token", "total_cost", "cancel_reason")
    inlines = (OrderItemInline,)

    @admin.display(description="Клиент")
    def customer(self, obj: Order):
        full_name = f"{obj.first_name} {obj.last_name}".strip()
        if obj.user:
            return format_html(
                "<strong>{}</strong><br><span style='color:#6b7280'>{}</span>",
                full_name or obj.user.username,
                obj.user.username,
            )
        return format_html(
            "<strong>{}</strong><br><span style='color:#6b7280'>{}</span>",
            full_name or "Гость",
            obj.email,
        )

    @admin.display(description="Статус", ordering="status")
    def status_badge(self, obj: Order):
        tone_map = {
            "pending": "warning",
            "processing": "info",
            "shipped": "accent",
            "delivered": "success",
            "cancelled": "danger",
        }
        return render_badge(obj.get_status_display(), tone_map.get(obj.status, "neutral"))

    @admin.display(description="Оплата", ordering="paid")
    def paid_badge(self, obj: Order):
        return render_badge("Оплачен", "success") if obj.paid else render_badge("Не оплачен", "danger")

    @admin.display(description="Итого")
    def total_cost(self, obj: Order):
        if not obj:
            return "0 ₽"
        return f"{obj.get_total_cost():.0f} ₽"

    @admin.display(description="Позиции")
    def items_count(self, obj: Order):
        return obj.items.count()

    @admin.action(description="Перевести выбранные заказы в 'В обработке'")
    def mark_processing(self, request, queryset):
        updated = queryset.update(status="processing")
        self.message_user(request, f"Заказов переведено в обработку: {updated}", level=messages.SUCCESS)

    @admin.action(description="Перевести выбранные заказы в 'Отправлен'")
    def mark_shipped(self, request, queryset):
        updated = queryset.update(status="shipped")
        self.message_user(request, f"Заказов помечено как отправленные: {updated}", level=messages.SUCCESS)

    @admin.action(description="Перевести выбранные заказы в 'Доставлен'")
    def mark_delivered(self, request, queryset):
        updated = queryset.update(status="delivered")
        self.message_user(request, f"Заказов помечено как доставленные: {updated}", level=messages.SUCCESS)

    @admin.action(description="Отменить выбранные заказы")
    def mark_cancelled(self, request, queryset):
        updated = queryset.update(status="cancelled")
        self.message_user(request, f"Заказов отменено: {updated}", level=messages.WARNING)

    @admin.action(description="Пометить выбранные заказы как оплаченные")
    def mark_paid(self, request, queryset):
        updated = queryset.update(paid=True)
        self.message_user(request, f"Заказов помечено как оплаченные: {updated}", level=messages.SUCCESS)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "product", "variant", "price", "quantity", "line_total")
    list_filter = ("order__created",)
    search_fields = ("order__id", "product__name", "variant__sku")
    autocomplete_fields = ("order", "product", "variant")
    list_select_related = ("order", "product", "variant")
    list_per_page = 25

    @admin.display(description="Сумма")
    def line_total(self, obj: OrderItem):
        return f"{obj.get_cost():.0f} ₽"
