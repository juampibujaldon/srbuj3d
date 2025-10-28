from decimal import Decimal

from rest_framework import serializers

from .models import (
    Admin,
    Cart,
    FeatureFlag,
    Filament,
    FilamentReservation,
    Machine,
    MachineJob,
    Order,
    OrderFile,
    OrderItem,
    Payment,
    Product,
    ProductImage,
    STLModel,
    Sell,
)


def _build_product_gallery(obj, request=None):
    urls = []

    def add(url):
        if not url:
            return
        if request:
            if url.startswith(("http://", "https://")):
                absolute = url
            else:
                absolute = request.build_absolute_uri(url)
        else:
            absolute = url
        if absolute and absolute not in urls:
            urls.append(absolute)

    gallery_manager = getattr(obj, "gallery", None)
    if gallery_manager is not None:
        for image in gallery_manager.all():
            if isinstance(image, ProductImage):
                if image.image:
                    add(image.image.url)
                if image.image_url:
                    add(image.image_url)

    if getattr(obj, "imagen", None):
        add(obj.imagen.url)
    if getattr(obj, "imagen_url", None):
        add(obj.imagen_url)

    return urls


class AdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Admin
        fields = "__all__"


class ProductSerializer(serializers.ModelSerializer):
    gallery = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = "__all__"
        extra_kwargs = {
            "imagen": {"required": False, "allow_null": True},
            "imagen_url": {"required": False, "allow_blank": True},
        }
        read_only_fields = ["gallery"]

    def get_gallery(self, obj):
        request = self.context.get("request") if hasattr(self, "context") else None
        return _build_product_gallery(obj, request)


class ProductPublicSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source="nombre")
    desc = serializers.CharField(source="descripcion", allow_blank=True, required=False)
    price = serializers.SerializerMethodField()
    img = serializers.SerializerMethodField()
    gallery = serializers.SerializerMethodField()
    author = serializers.CharField(source="autor", allow_blank=True, required=False)
    weightGr = serializers.IntegerField(source="peso_gr", required=False)
    featured = serializers.BooleanField(source="mostrar_inicio", required=False)

    class Meta:
        model = Product
        fields = [
            "id",
            "title",
            "author",
            "img",
            "gallery",
            "price",
            "desc",
            "stock",
            "weightGr",
            "categoria",
            "featured",
        ]

    def get_price(self, obj):
        return float(obj.precio) if obj.precio is not None else None

    def get_img(self, obj):
        request = self.context.get("request") if hasattr(self, "context") else None
        gallery = _build_product_gallery(obj, request)
        if gallery:
            return gallery[0]
        return ""

    def get_gallery(self, obj):
        request = self.context.get("request") if hasattr(self, "context") else None
        return _build_product_gallery(obj, request)


class ProductMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "nombre", "precio", "imagen_url"]

    nombre = serializers.CharField(read_only=True)
    precio = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)


class OrderItemSerializer(serializers.ModelSerializer):
    product_id = serializers.PrimaryKeyRelatedField(
        source="product",
        queryset=Product.objects.all(),
        allow_null=True,
        required=False,
    )
    product = ProductMiniSerializer(read_only=True)
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "product_id",
            "title",
            "sku",
            "quantity",
            "unit_price",
            "metadata",
            "line_total",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "product", "line_total", "created_at", "updated_at"]

    def get_line_total(self, obj):
        return float(obj.unit_price * obj.quantity)


class OrderFileSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    uploaded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = OrderFile
        fields = [
            "id",
            "original_name",
            "file",
            "file_url",
            "preview_url",
            "notes",
            "uploaded_by",
            "uploaded_by_name",
            "uploaded_ip",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "file",
            "file_url",
            "uploaded_by",
            "uploaded_by_name",
            "uploaded_ip",
            "created_at",
            "updated_at",
        ]

    def get_file_url(self, obj):
        request = self.context.get("request") if hasattr(self, "context") else None
        if request:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url

    def get_uploaded_by_name(self, obj):
        if obj.uploaded_by:
            return obj.uploaded_by.get_full_name() or obj.uploaded_by.username
        return ""


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, required=False)
    files = OrderFileSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    customer = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "user",
            "status",
            "status_display",
            "subtotal",
            "shipping_cost",
            "total",
            "shipping_address",
            "billing_address",
            "shipping_quote",
            "payment_metadata",
            "submitted_at",
            "paid_at",
            "cancelled_at",
            "fulfilled_at",
            "notes",
            "items",
            "files",
            "customer",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "subtotal",
            "total",
            "submitted_at",
            "paid_at",
            "cancelled_at",
            "fulfilled_at",
            "created_at",
            "updated_at",
            "status_display",
            "customer",
        ]

    def get_customer(self, obj):
        return obj.get_customer_name()

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        order = Order.objects.create(**validated_data)
        self._upsert_items(order, items_data)
        order.refresh_amounts()
        return order

    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if items_data is not None:
            instance.items.all().delete()
            self._upsert_items(instance, items_data)
        instance.refresh_amounts()
        return instance

    def _upsert_items(self, order, items_data):
        for payload in items_data:
            product = payload.get("product")
            quantity_raw = payload.get("quantity") or 1
            try:
                quantity = max(1, int(quantity_raw))
            except (TypeError, ValueError):
                quantity = 1
            try:
                unit_price = Decimal(str(payload.get("unit_price") or 0))
            except (TypeError, ValueError, ArithmeticError):
                unit_price = Decimal("0")

            OrderItem.objects.create(
                order=order,
                product=product,
                title=payload.get("title") or "",
                sku=payload.get("sku") or "",
                quantity=quantity,
                unit_price=unit_price,
                metadata=payload.get("metadata") or {},
            )


class OrderListSerializer(OrderSerializer):
    class Meta(OrderSerializer.Meta):
        fields = [
            "id",
            "status",
            "status_display",
            "subtotal",
            "shipping_cost",
            "total",
            "submitted_at",
            "paid_at",
            "fulfilled_at",
            "cancelled_at",
            "customer",
            "shipping_address",
            "shipping_quote",
            "created_at",
            "updated_at",
            "items",
            "files",
        ]


class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = "__all__"


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"


class STLModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = STLModel
        fields = "__all__"


class SellSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sell
        fields = "__all__"


class OrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["status"]


class FeatureFlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureFlag
        fields = ["id", "key", "enabled", "description", "updated_at"]
        read_only_fields = ["id", "updated_at", "description"]


class FilamentSnapshotSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    gramsAvailable = serializers.IntegerField(source="grams_available")
    gramsReserved = serializers.IntegerField(source="grams_reserved")
    freeGrams = serializers.SerializerMethodField()
    reorderPointGrams = serializers.IntegerField(source="reorder_point_grams")
    gramsPerUnit = serializers.IntegerField(source="grams_per_unit")
    estPrintMinPerUnit = serializers.IntegerField(source="est_print_min_per_unit")

    class Meta:
        model = Filament
        fields = [
            "id",
            "sku",
            "material",
            "color",
            "diameter",
            "gramsAvailable",
            "gramsReserved",
            "freeGrams",
            "reorderPointGrams",
            "gramsPerUnit",
            "estPrintMinPerUnit",
            "notes",
        ]

    def get_id(self, obj):
        return obj.external_id or obj.pk

    def get_freeGrams(self, obj):
        return obj.free_grams


class MachineJobSnapshotSerializer(serializers.ModelSerializer):
    estMinutesPerUnit = serializers.IntegerField(source="est_minutes_per_unit")
    remainingMinutes = serializers.IntegerField(source="remaining_minutes")
    qty = serializers.IntegerField(source="quantity")

    class Meta:
        model = MachineJob
        fields = [
            "id",
            "sku",
            "title",
            "qty",
            "estMinutesPerUnit",
            "remainingMinutes",
            "position",
        ]


class MachineSnapshotSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="identifier")
    maintenanceEveryHours = serializers.IntegerField(source="maintenance_every_hours")
    maintenanceHoursUsed = serializers.IntegerField(source="maintenance_hours_used")
    avgSpeedFactor = serializers.DecimalField(source="avg_speed_factor", max_digits=5, decimal_places=2)
    queue = MachineJobSnapshotSerializer(many=True, source="jobs")
    queueEtaMinutes = serializers.SerializerMethodField()
    compatibleMaterials = serializers.ListField(source="compatible_materials")

    class Meta:
        model = Machine
        fields = [
            "id",
            "name",
            "model",
            "status",
            "nozzle",
            "avgSpeedFactor",
            "maintenanceEveryHours",
            "maintenanceHoursUsed",
            "queueEtaMinutes",
            "compatibleMaterials",
            "queue",
        ]

    def get_queueEtaMinutes(self, obj):
        return obj.queue_eta_minutes


class FilamentReservationSerializer(serializers.ModelSerializer):
    filamentSku = serializers.CharField(source="filament.sku", read_only=True)
    filamentId = serializers.SerializerMethodField()

    class Meta:
        model = FilamentReservation
        fields = [
            "id",
            "order_id",
            "filamentId",
            "filamentSku",
            "grams",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "filamentSku", "filamentId", "created_at", "updated_at"]

    def get_filamentId(self, obj):
        return obj.filament.external_id or obj.filament.pk
