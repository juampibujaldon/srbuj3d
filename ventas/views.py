from django.shortcuts import render
from rest_framework import viewsets
from .serializer import *
from .models import *  
from rest_framework import viewsets
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
# from ventas_user_admin.views import IsCompanyAdmin
from .models import Admin, Product, Order, Cart, Payment, STLModel, Sell  
from .serializer import (
    AdminSerializer,
    ProductSerializer,
    OrderSerializer,
    CartSerializer,
    PaymentSerializer,
    STLModelSerializer,
    SellSerializer,
)
from django.contrib.auth.models import AbstractUser
from .models import User

class AdminView(viewsets.ModelViewSet):
    serializer_class = AdminSerializer
    queryset = Admin.objects.all()
    permission_classes = [IsAuthenticated]

class ProductView(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    queryset = Product.objects.all()
    permission_classes = [IsAuthenticated]

class OrderView(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    queryset = Order.objects.all()
    permission_classes = [IsAuthenticated]

class CartView(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    queryset = Cart.objects.all()
    permission_classes = [IsAuthenticated]

class PaymentView(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    queryset = Payment.objects.all()
    permission_classes = [IsAuthenticated]

class STLModelView(viewsets.ModelViewSet):
    serializer_class = STLModelSerializer
    queryset = STLModel.objects.all()
    permission_classes = [IsAuthenticated]

class SellView(viewsets.ModelViewSet):
    serializer_class = SellSerializer
    queryset = Sell.objects.all()
    permission_classes = [IsAuthenticated]

# class User(AbstractUser):
#     nombre = models.CharField(max_length=100)
#     email = models.EmailField(unique=True)
#     contraseña = models.CharField(max_length=255)

#     groups = models.ManyToManyField(
#         'auth.Group',
#         related_name='ventas_user_groups',  # Cambia el related_name para evitar conflictos
#         blank=True,
#         help_text='The groups this user belongs to.',
#         verbose_name='groups',
#     )
#     user_permissions = models.ManyToManyField(
#         'auth.Permission',
#         related_name='ventas_user_permissions',  # Cambia el related_name para evitar conflictos
#         blank=True,
#         help_text='Specific permissions for this user.',
#         verbose_name='user permissions',
#     )

#     def __str__(self):
#         return self.nombre