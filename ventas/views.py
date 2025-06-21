from rest_framework import viewsets, generics, permissions, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, permissions
from .models import Order
from .serializer import OrderPanelSerializer
from .models import User, Admin, Product, Order, Cart, Payment, STLModel, Sell
from .serializer import (
    AdminSerializer,
    ProductSerializer,
    OrderSerializer,
    CartSerializer,
    PaymentSerializer,
    STLModelSerializer,
    SellSerializer,
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
    # serializer_class = ProductSerializer
    # def get_queryset(self):
    #     return Product.objects.filter(activo=True)

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