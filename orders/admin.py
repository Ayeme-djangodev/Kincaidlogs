from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "quantity", "unit_price", "line_total")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "customer",
        "full_name",
        "total",
        "status",
        "created_at",
    )

    list_filter = ("status", "created_at")

    search_fields = (
        "full_name",
        "email",
        "phone",
        "customer__username",
        "customer__email",
    )

    list_editable = ("status",)

    readonly_fields = ("customer", "full_name", "email", "phone", "total", "created_at", "updated_at")

    inlines = [OrderItemInline]

    date_hierarchy = "created_at"
