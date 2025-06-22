from django.db import models
from ventas_user_admin.models import User

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
    stock = models.IntegerField()
    activo = models.BooleanField(default=True)
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)  # Opcional

    def __str__(self):
        return self.nombre

class Order(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('procesando', 'Procesando'),
        ('enviado', 'Enviado'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha = models.DateField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='pendiente')
    direccion_envio = models.CharField(max_length=255, blank=True, null=True)  # Para tipo de envío
    product = models.ForeignKey('Product', on_delete=models.CASCADE, null=True, blank=True)  # Para panel y facturas
    cantidad = models.PositiveIntegerField(default=1)  # Para panel y facturas

    def __str__(self):
        return f'Pedido {self.id} - {self.user}'

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()

    def __str__(self):
        return f'{self.cantidad} x {self.product.nombre} - {self.user}'

class PaymentMethod(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    def __str__(self):
        return self.nombre

class Payment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    metodo = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True)
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
    ]
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='pendiente')

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
        return f'Venta {self.id} - {self.product.nombre} ({self.cantidad})'

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    def __str__(self):
        return f'{self.user} - {self.product.nombre}'