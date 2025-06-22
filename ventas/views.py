from rest_framework import viewsets, generics, permissions, serializers, status, filters
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from django.core.mail import send_mail
from django.http import FileResponse
from .models import (
    User, Admin, Product, Order, Cart, Payment, STLModel, Sell, PaymentMethod, Wishlist
)
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from .models import Order
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
    WishlistSerializer,
)
# ------------------- PRODUCTOS -------------------

class ProductCreateView(generics.CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminUser]

class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class ProductUpdateView(generics.UpdateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminUser]

class ProductDeleteView(generics.DestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminUser]

class ProductListView(generics.ListAPIView):
    queryset = Product.objects.filter(activo=True)
    serializer_class = ProductSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'descripcion']
    ordering_fields = ['precio', 'stock']

# ------------------- CARRITO -------------------

class CartAddView(generics.CreateAPIView):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class CartListView(generics.ListAPIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

class CartCheckoutView(APIView):
    permission_classes = [IsAuthenticated]

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
                estado='pendiente'
            )
            orders.append(order)
        cart_items.delete()
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

# ------------------- PEDIDOS -------------------

class UserOrderHistoryView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

class OrderPanelView(generics.ListAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderPanelSerializer
    permission_classes = [IsAdminUser]

class OrderStatusUpdateView(generics.UpdateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAdminUser]

    def patch(self, request, *args, **kwargs):
        response = self.partial_update(request, *args, **kwargs)
        # Notificación por email al usuario
        order = self.get_object()
        send_mail(
            'Estado de tu pedido actualizado',
            f'Tu pedido #{order.id} ahora está en estado: {order.estado}',
            'no-reply@tuapp.com',
            [order.user.email],
        )
        return response

class OrderTrackingView(generics.RetrieveAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

# ------------------- WISHLIST -------------------

class WishlistAddView(generics.CreateAPIView):
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticated]
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class WishlistListView(generics.ListAPIView):
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)

# ------------------- MÉTODOS DE PAGO -------------------

class PaymentMethodListView(generics.ListAPIView):
    queryset = PaymentMethod.objects.filter(activo=True)
    serializer_class = PaymentMethodSerializer
    permission_classes = [permissions.AllowAny]

# ------------------- DASHBOARD ADMIN -------------------

class SalesDashboardView(APIView):
    permission_classes = [IsAdminUser]
    def get(self, request):
        total_ventas = Order.objects.count()
        total_ingresos = Order.objects.aggregate(serializers.Sum('total'))['total__sum'] or 0
        productos_mas_vendidos = Product.objects.order_by('-order__cantidad')[:5]
        return Response({
            "total_ventas": total_ventas,
            "total_ingresos": total_ingresos,
            "productos_mas_vendidos": [p.nombre for p in productos_mas_vendidos],
        })

# ------------------- RECOMENDACIONES -------------------

class ProductRecommendationView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        productos = Product.objects.order_by('-order__cantidad')[:5]
        serializer = ProductSerializer(productos, many=True)
        return Response(serializer.data)

# ------------------- FACTURA PDF (ejemplo simple) -------------------

def generate_invoice(request, order_id):
    order = Order.objects.get(pk=order_id)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="factura_{order_id}.pdf"'

    p = canvas.Canvas(response)
    p.drawString(100, 800, f"Factura para pedido #{order.id}")
    p.drawString(100, 780, f"Cliente: {order.user.get_full_name()}")
    p.drawString(100, 760, f"Producto: {order.product.nombre}")
    p.drawString(100, 740, f"Cantidad: {order.cantidad}")
    p.drawString(100, 720, f"Total: ${order.total}")
    # ...agrega más datos según tu modelo...
    p.showPage()
    p.save()
    return response

# ------------------- MERCADOPAGO (ejemplo simple) -------------------
import mercadopago
class MercadoPagoInitView(APIView):
    def post(self, request):
        sdk = mercadopago.SDK("TU_ACCESS_TOKEN")   #! ver esto bien
        preference_data = {
            "items": [
                 {
                     "title": "Producto",
                     "quantity": 1,
                     "unit_price": 100
                 }
            ]
        }
        preference_response = sdk.preference().create(preference_data)
        return Response(preference_response["response"])
    
class AdminView(viewsets.ModelViewSet):
    queryset = Admin.objects.all()
    serializer_class = AdminSerializer
    permission_classes = [permissions.IsAdminUser]

    
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAdminUser]

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAdminUser] 
class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class AdminViewSet(viewsets.ModelViewSet):
    queryset = Admin.objects.all()
    serializer_class = AdminSerializer
    permission_classes = [permissions.IsAdminUser]

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

class STLModelViewSet(viewsets.ModelViewSet):
    queryset = STLModel.objects.all()
    serializer_class = STLModelSerializer

class SellViewSet(viewsets.ModelViewSet):
    queryset = Sell.objects.all()
    serializer_class = SellSerializer

class ProtectedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'message': f'Hola, {request.user.username}. Estás autenticado con JWT!'})
