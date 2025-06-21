from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.hashers import make_password
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

    def __str__(self):
        return f'Pedido {self.id} - {self.usuario.nombre}'

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()

    def __str__(self):
        return f'{self.cantidad} x {self.producto.nombre} - {self.usuario.nombre}'

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

    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    metodo = models.CharField(max_length=20, choices=METODO_CHOICES)
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='pendiente')

    def __str__(self):
        return f'Pago {self.id} - {self.pedido.id} ({self.estado})'

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
        return f'Venta {self.id} - {self.producto.nombre} ({self.cantidad})'
        
