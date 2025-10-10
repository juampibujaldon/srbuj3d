from django.db import models

from ventas_user_admin.models import User


class TimeStampedModel(models.Model):
    """Abstract base model that stores creation/update timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Admin(models.Model):
    nombre = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    contraseña = models.CharField(max_length=255)

    def __str__(self):
        return self.nombre

class Product(models.Model):
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    autor = models.CharField(max_length=255, blank=True, default="SrBuj")
    categoria = models.CharField(max_length=120, blank=True, default="General")
    imagen_url = models.URLField(blank=True, null=True)
    imagen = models.ImageField(upload_to="products/", blank=True, null=True)
    peso_gr = models.PositiveIntegerField(default=300)
    mostrar_inicio = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="gallery",
    )
    image = models.ImageField(upload_to="products/gallery/", blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    position = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["position", "id"]

    def __str__(self):
        return f"Imagen de {self.product.nombre} ({self.id})"

class Order(TimeStampedModel):
    """Represents a printable order tied to a customer and printable files."""

    STATUS_DRAFT = "draft"
    STATUS_PENDING = "pending"
    STATUS_PAID = "paid"
    STATUS_CANCELLED = "cancelled"
    STATUS_FULFILLED = "fulfilled"

    STATUS_CHOICES = [
        (STATUS_DRAFT, "Borrador"),
        (STATUS_PENDING, "Pendiente"),
        (STATUS_PAID, "Pagado"),
        (STATUS_CANCELLED, "Cancelado"),
        (STATUS_FULFILLED, "Completado"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
    )
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_address = models.JSONField(default=dict, blank=True)
    shipping_quote = models.JSONField(default=dict, blank=True)
    billing_address = models.JSONField(default=dict, blank=True)
    payment_metadata = models.JSONField(default=dict, blank=True)
    submitted_at = models.DateTimeField(blank=True, null=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)
    fulfilled_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        ref = str(self.id).zfill(6) if self.id else "nuevo"
        return f"Pedido #{ref} - {self.get_customer_name()}"

    def get_customer_name(self):
        if self.user and self.user.get_full_name():
            return self.user.get_full_name()
        if self.user:
            return self.user.username
        return self.shipping_address.get("nombre") or self.shipping_address.get("email") or "Cliente sin nombre"

    @property
    def currency(self):
        return self.shipping_quote.get("currency", "ARS")

    def refresh_amounts(self, commit=True):
        from django.db.models import DecimalField, F, Sum

        aggregates = self.items.aggregate(
            subtotal=Sum(
                models.ExpressionWrapper(
                    F("unit_price") * F("quantity"),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                )
            )
        )
        subtotal = aggregates.get("subtotal") or 0
        self.subtotal = subtotal
        self.total = subtotal + (self.shipping_cost or 0)
        if commit:
            self.save(update_fields=["subtotal", "total", "updated_at"])


class OrderItem(TimeStampedModel):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
    )
    title = models.CharField(max_length=255)
    sku = models.CharField(max_length=120, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.CheckConstraint(
                check=models.Q(quantity__gte=1),
                name="order_item_quantity_positive",
            )
        ]

    def __str__(self):
        return f"{self.quantity} x {self.title}"

    @property
    def line_total(self):
        return self.unit_price * self.quantity


def order_file_upload_path(instance, filename):
    return f"custom/{instance.order_id}/{filename}"


class OrderFile(TimeStampedModel):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="files",
    )
    file = models.FileField(upload_to=order_file_upload_path)
    original_name = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_files",
    )
    notes = models.TextField(blank=True)
    preview_url = models.URLField(blank=True)
    uploaded_ip = models.GenericIPAddressField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.original_name} (Orden {self.order_id})"


class FeatureFlag(TimeStampedModel):
    key = models.CharField(max_length=120, unique=True)
    enabled = models.BooleanField(default=False)
    description = models.CharField(max_length=255, blank=True)
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="feature_flags",
    )

    class Meta:
        verbose_name = "Feature flag"
        verbose_name_plural = "Feature flags"
        ordering = ["key"]

    def __str__(self):
        state = "on" if self.enabled else "off"
        return f"{self.key} ({state})"

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.cantidad} x {self.product.nombre}"

class Payment(models.Model):
    METODO_CHOICES = [
        ('tarjeta', 'Tarjeta'),
        ('transferencia', 'Transferencia'),
        ('paypal', 'PayPal'),
        ('mercadopago', 'MercadoPago'),
        ('otro', 'Otro'),
    ]

    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments")
    metodo = models.CharField(max_length=20, choices=METODO_CHOICES)
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='pendiente')

    def __str__(self):
        return f"Pago {self.id} - {self.order_id} ({self.estado})"

class STLModel(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    nombre_archivo = models.CharField(max_length=255)
    costo = models.DecimalField(max_digits=10, decimal_places=2)
    tiempo_estimado = models.FloatField()

    def __str__(self):
        return self.nombre_archivo

class Sell(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    fecha = models.DateField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    def __str__(self):
        return f"Venta {self.id} - {self.product.nombre} ({self.cantidad})"
        
