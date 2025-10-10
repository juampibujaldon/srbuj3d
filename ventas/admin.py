from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Admin,
    Cart,
    FeatureFlag,
    Order,
    OrderFile,
    OrderItem,
    Payment,
    Product,
    ProductImage,
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


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0
    fields = ("preview", "image", "image_url", "position")
    readonly_fields = ("preview",)

    def preview(self, instance):
        if instance.image:
            return format_html('<img src="{}" style="max-height:80px;"/>', instance.image.url)
        if instance.image_url:
            return format_html('<img src="{}" style="max-height:80px;"/>', instance.image_url)
        return "—"

    preview.short_description = "Vista previa"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "categoria", "precio", "stock", "mostrar_inicio")
    list_filter = ("categoria", "mostrar_inicio")
    search_fields = ("nombre", "autor", "categoria")
    inlines = [ProductImageInline]


admin.site.register(Admin)
admin.site.register(Cart)
admin.site.register(Payment)
admin.site.register(STLModel)
admin.site.register(Sell)
admin.site.register(
    FeatureFlag,
    list_display=("key", "enabled", "updated_by", "updated_at"),
    list_editable=("enabled",),
)
