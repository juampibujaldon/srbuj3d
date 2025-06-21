from rest_framework import viewsets, generics, permissions, serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction

from .models import User, Admin, Product, Order, Cart, Payment, STLModel, Sell, PaymentMethod
from .serializer import (
    AdminSerializer,
    ProductSerializer,
    OrderSerializer,
    CartSerializer,
    PaymentSerializer,
    STLModelSerializer,
    SellSerializer,
    PaymentMethodSerializer,
    OrderPanelSerializer,
)

# Crear producto (con stock inicial)
class ProductCreateView(generics.CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAdminUser]

# Leer producto (ver stock)
class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

# Actualizar producto (actualizar stock)
class ProductUpdateView(generics.UpdateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAdminUser]

# Eliminar producto (solo si es seguro)
class ProductDeleteView(generics.DestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAdminUser]

class ProductListView(generics.ListAPIView):
    queryset = Product.objects.filter(activo=True)
    serializer_class = ProductSerializer

class OrderCreateView(generics.CreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        product_id = self.request.data.get('product')  # Ajusta el nombre según tu serializer
        cantidad = int(self.request.data.get('cantidad', 1))
        product = Product.objects.get(id=product_id)
        if product.stock >= cantidad:
            product.stock -= cantidad
            product.save()
            serializer.save(user=self.request.user, total=product.precio * cantidad)
        else:
            raise serializers.ValidationError("Stock insuficiente")
        
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

class CartAddView(generics.CreateAPIView):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class CartListView(generics.ListAPIView):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

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

class OrderPanelView(generics.ListAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderPanelSerializer
    permission_classes = [permissions.IsAdminUser] 

class PaymentMethodListView(generics.ListAPIView):
    queryset = PaymentMethod.objects.filter(activo=True)
    serializer_class = PaymentMethodSerializer
    permission_classes = [permissions.AllowAny]

class CartCheckoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        user = request.user
        cart_items = Cart.objects.filter(user=user)
        if not cart_items.exists():
            return Response({"detail": "El carrito está vacío."}, status=status.HTTP_400_BAD_REQUEST)

        orders = []
        for item in cart_items:
            product = item.product
            if product.stock < item.cantidad:
                return Response({"detail": f"Stock insuficiente para {product.nombre}."}, status=status.HTTP_400_BAD_REQUEST)
            product.stock -= item.cantidad
            product.save()
            order = Order.objects.create(
                user=user,
                product=product,
                cantidad=item.cantidad,
                total=product.precio * item.cantidad,
                # agrega otros campos necesarios aquí
            )
            orders.append(order)
        cart_items.delete()
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)