from rest_framework import serializers
from .models import *

class AdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Admin
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"
        extra_kwargs = {
            "imagen": {"required": False, "allow_null": True},
            "imagen_url": {"required": False, "allow_blank": True},
        }


class ProductPublicSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source="nombre")
    desc = serializers.CharField(source="descripcion", allow_blank=True, required=False)
    price = serializers.SerializerMethodField()
    img = serializers.SerializerMethodField()
    author = serializers.CharField(source="autor", allow_blank=True, required=False)
    weightGr = serializers.IntegerField(source="peso_gr", required=False)

    class Meta:
        model = Product
        fields = [
            "id",
            "title",
            "author",
            "img",
            "price",
            "desc",
            "stock",
            "likes",
            "downloads",
            "weightGr",
            "categoria",
        ]

    def get_price(self, obj):
        return float(obj.precio) if obj.precio is not None else None

    def get_img(self, obj):
        request = self.context.get("request") if hasattr(self, "context") else None
        if getattr(obj, "imagen", None):
            url = obj.imagen.url
            if request:
                return request.build_absolute_uri(url)
            return url
        return obj.imagen_url or ""

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = "__all__"


class OrderPublicSerializer(serializers.ModelSerializer):
    total = serializers.SerializerMethodField()
    subtotal = serializers.SerializerMethodField()
    customer = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    items = serializers.SerializerMethodField()
    payment = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "fecha",
            "estado",
            "subtotal",
            "total",
            "items",
            "customer",
            "email",
            "shipping",
            "shipping_quote",
            "payment",
        ]

    def get_total(self, obj):
        return float(obj.total)

    def get_subtotal(self, obj):
        return float(obj.subtotal)

    def get_customer(self, obj):
        if obj.user and obj.user.get_full_name():
            return obj.user.get_full_name()
        if obj.shipping:
            return obj.shipping.get("nombre") or obj.shipping.get("email")
        return obj.user.username if obj.user else ""

    def get_email(self, obj):
        if obj.shipping:
            return obj.shipping.get("email", "")
        if obj.user:
            return obj.user.email
        return ""

    def get_items(self, obj):
        return obj.items or []

    def get_payment(self, obj):
        return obj.payment_info or {}

class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = '__all__'

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'

class STLModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = STLModel
        fields = '__all__'


class SellSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sell
        fields = '__all__'


class OrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["estado"]
