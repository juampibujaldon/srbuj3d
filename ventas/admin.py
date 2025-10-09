from django.contrib import admin

from .models import (
    Admin,
    Cart,
    FeatureFlag,
    Order,
    OrderFile,
    OrderItem,
    Payment,
    Product,
    STLModel,
    Sell,
)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("created_at", "updated_at")


class OrderFileInline(admin.TabularInline):
    model = OrderFile
    extra = 0
    readonly_fields = ("original_name", "uploaded_by", "uploaded_ip", "created_at", "updated_at")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "user", "subtotal", "shipping_cost", "total", "submitted_at", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("id", "user__username", "user__email")
    autocomplete_fields = ("user",)
    inlines = [OrderItemInline, OrderFileInline]


admin.site.register(Admin)
admin.site.register(Product)
admin.site.register(Cart)
admin.site.register(Payment)
admin.site.register(STLModel)
admin.site.register(Sell)
admin.site.register(
    FeatureFlag,
    list_display=("key", "enabled", "updated_by", "updated_at"),
    list_editable=("enabled",),
)
