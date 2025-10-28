from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

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


class Filament(TimeStampedModel):
    """Representa un filamento o lote de material controlado en stock."""

    external_id = models.CharField(
        max_length=120,
        blank=True,
        null=True,
        unique=True,
        help_text="Identificador amigable opcional usado por la interfaz.",
    )
    sku = models.CharField(max_length=120, unique=True)
    material = models.CharField(max_length=120)
    color = models.CharField(max_length=120)
    diameter = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=Decimal("1.75"),
        validators=[MinValueValidator(Decimal("0.10"))],
    )
    grams_available = models.PositiveIntegerField(default=0)
    grams_reserved = models.PositiveIntegerField(default=0)
    reorder_point_grams = models.PositiveIntegerField(default=0)
    grams_per_unit = models.PositiveIntegerField(
        default=0,
        help_text="Consumo estimado por pieza en gramos.",
    )
    est_print_min_per_unit = models.PositiveIntegerField(
        default=0,
        help_text="Tiempo estimado por pieza en minutos.",
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["material", "color", "sku"]

    def __str__(self):
        return f"{self.sku} ({self.material} {self.color})"

    @property
    def free_grams(self) -> int:
        return max(self.grams_available - self.grams_reserved, 0)

    def adjust(self, delta: int, commit: bool = True):
        new_total = int(self.grams_available) + int(delta)
        if new_total < self.grams_reserved:
            raise ValueError("No podés dejar el stock por debajo de las reservas")
        self.grams_available = max(new_total, 0)
        if commit:
            self.save(update_fields=["grams_available", "updated_at"])


class Machine(TimeStampedModel):
    """Representa una impresora o máquina con una cola de trabajos."""

    STATUS_ONLINE = "online"
    STATUS_MAINTENANCE = "maintenance"
    STATUS_OFFLINE = "offline"

    STATUS_CHOICES = [
        (STATUS_ONLINE, "online"),
        (STATUS_MAINTENANCE, "maintenance"),
        (STATUS_OFFLINE, "offline"),
    ]

    identifier = models.CharField(
        max_length=120,
        unique=True,
        help_text="Identificador legible usado por el panel.",
    )
    name = models.CharField(max_length=255)
    model = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ONLINE,
    )
    nozzle = models.CharField(max_length=20, blank=True)
    avg_speed_factor = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("1.00"),
        validators=[MinValueValidator(Decimal("0.10"))],
    )
    maintenance_every_hours = models.PositiveIntegerField(default=120)
    maintenance_hours_used = models.PositiveIntegerField(default=0)
    last_maintenance_at = models.DateTimeField(blank=True, null=True)
    compatible_materials = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["identifier"]

    def __str__(self):
        return self.name

    @property
    def queue_eta_minutes(self) -> int:
        return sum(job.effective_minutes for job in self.jobs.all())

    def register_maintenance(self, commit: bool = True):
        self.maintenance_hours_used = 0
        self.last_maintenance_at = timezone.now()
        if commit:
            self.save(update_fields=["maintenance_hours_used", "last_maintenance_at", "updated_at"])

    def maintenance_ratio(self) -> float:
        if not self.maintenance_every_hours:
            return 0
        return self.maintenance_hours_used / self.maintenance_every_hours


class MachineJob(TimeStampedModel):
    """Trabajo individual asignado a una máquina."""

    machine = models.ForeignKey(
        Machine,
        on_delete=models.CASCADE,
        related_name="jobs",
    )
    sku = models.CharField(max_length=120, blank=True)
    title = models.CharField(max_length=255, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    est_minutes_per_unit = models.PositiveIntegerField(default=0)
    remaining_minutes = models.PositiveIntegerField(default=0)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]

    def __str__(self):
        return f"{self.machine.identifier} - {self.sku or 'job'} ({self.quantity})"

    @property
    def effective_minutes(self) -> int:
        value = self.remaining_minutes or 0
        if value <= 0 and self.est_minutes_per_unit:
            value = self.est_minutes_per_unit * max(self.quantity, 1)
        return max(value, 0)


class FilamentReservation(TimeStampedModel):
    """Reserva de gramos de filamento ligada a un pedido."""

    order_id = models.CharField(max_length=64)
    filament = models.ForeignKey(
        Filament,
        on_delete=models.CASCADE,
        related_name="reservations",
    )
    grams = models.PositiveIntegerField()
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["order_id", "filament"],
                name="unique_reservation_per_filament_and_order",
            )
        ]

    def __str__(self):
        return f"Reserva {self.order_id} - {self.filament.sku} ({self.grams}g)"
