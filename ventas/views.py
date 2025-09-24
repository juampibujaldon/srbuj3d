from decimal import Decimal

from django.db.models import Sum
from django.shortcuts import render
from rest_framework import viewsets, generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response

from .models import Admin, Product, Order, Cart, Payment, STLModel, Sell, User
from .serializer import (
    AdminSerializer,
    ProductSerializer,
    ProductPublicSerializer,
    OrderSerializer,
    OrderPublicSerializer,
    OrderStatusSerializer,
    CartSerializer,
    PaymentSerializer,
    STLModelSerializer,
    SellSerializer,
)

class AdminView(viewsets.ModelViewSet):
    serializer_class = AdminSerializer
    queryset = Admin.objects.all()
    permission_classes = [IsAuthenticated]

class ProductView(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    queryset = Product.objects.all()
    permission_classes = [IsAuthenticated]


def _is_admin(user):
    return bool(user and user.is_authenticated and getattr(user, "role", "") == "admin")


def _require_admin(user):
    if not _is_admin(user):
        raise PermissionDenied("Solo los administradores pueden realizar esta acción.")


SAMPLE_PRODUCTS = [
    {
        "nombre": "Escultura David Neo",
        "autor": "SrBuj",
        "imagen_url": "/images/david.jpeg",
        "likes": 124,
        "downloads": 342,
        "precio": Decimal("3500"),
        "descripcion": "Mini escultura del David con acabado neo; ideal para escritorio o estantería.",
    },
    {
        "nombre": "Mate Hogwarts",
        "autor": "SrBuj",
        "imagen_url": "/images/mate%20hogwarts.jpeg",
        "likes": 218,
        "downloads": 552,
        "precio": Decimal("8900"),
        "descripcion": "Mate temático inspirado en Hogwarts. Perfecto para fans.",
    },
    {
        "nombre": "Mate Canon",
        "autor": "SrBuj",
        "imagen_url": "/images/mate%20canon.jpeg",
        "likes": 175,
        "downloads": 410,
        "precio": Decimal("8700"),
        "descripcion": "Mate con estética fotográfica estilo Canon.",
    },
    {
        "nombre": "Joyero Ajedrez",
        "autor": "SrBuj",
        "imagen_url": "/images/joyero%20ajedrez.jpeg",
        "likes": 142,
        "downloads": 398,
        "precio": Decimal("12500"),
        "descripcion": "Caja/joyero inspirado en el ajedrez con compartimentos internos.",
    },
    {
        "nombre": "Set Ajedrez Minimal",
        "autor": "SrBuj",
        "imagen_url": "/images/ser%20ajedrez.jpeg",
        "likes": 289,
        "downloads": 720,
        "precio": Decimal("48000"),
        "descripcion": "Set de ajedrez impreso en 3D estilo minimal.",
    },
]


def _ensure_seed_data():
    if not Product.objects.exists():
        Product.objects.bulk_create(Product(**data) for data in SAMPLE_PRODUCTS)


class ProductListCreateView(generics.ListCreateAPIView):
    queryset = Product.objects.all().order_by("id")
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_class(self):
        if self.request.method == "GET" and _is_admin(self.request.user):
            return ProductSerializer
        if self.request.method == "GET":
            return ProductPublicSerializer
        return ProductSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        _ensure_seed_data()
        return super().get_queryset()

    def perform_create(self, serializer):
        _require_admin(self.request.user)
        serializer.save()


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_class(self):
        if self.request.method == "GET" and _is_admin(self.request.user):
            return ProductSerializer
        if self.request.method == "GET":
            return ProductPublicSerializer
        return ProductSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        _ensure_seed_data()
        return super().get_queryset()

    def perform_update(self, serializer):
        _require_admin(self.request.user)
        serializer.save()

    def perform_destroy(self, instance):
        _require_admin(self.request.user)
        instance.delete()


class OrderListView(generics.ListAPIView):
    serializer_class = OrderPublicSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not _is_admin(self.request.user):
            raise PermissionDenied("Solo los administradores pueden ver las órdenes")
        return Order.objects.order_by("-fecha")


class OrderStatusUpdateView(generics.UpdateAPIView):
    serializer_class = OrderStatusSerializer
    permission_classes = [IsAuthenticated]
    queryset = Order.objects.all()

    def perform_update(self, serializer):
        _require_admin(self.request.user)
        serializer.save()

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


# --- Endpoints simplificados para el frontend público ---

@api_view(["POST"])
@permission_classes([AllowAny])
def cotizar_andreani(request):
    """
    Calcula una cotización simple de envío en base al peso y devuelve ETA.
    Espera JSON con: { cpDestino, provincia, localidad, tipo, pesoGr, altoCm, anchoCm, largoCm }
    Responde: { precio: number, eta: string }
    """
    try:
        data = request.data or {}
        peso_gr = float(data.get("pesoGr", 0) or 0)
        # Tarifa base + variable por kg
        base = 2500
        variable = 800 * max(peso_gr / 1000.0, 0)
        precio = round(base + variable)
        eta = "3-5 días hábiles"
        return Response({"precio": precio, "eta": eta})
    except Exception as e:
        return Response({"detail": "Error al cotizar"}, status=400)


@api_view(["POST"])
@permission_classes([AllowAny])
def crear_orden(request):
    """
    Crea una orden de forma simplificada y devuelve (opcionalmente) una URL de pago.
    Espera JSON con: { items: [...], shipping: {...}, shippingQuote: {...}, payment: {...}, subtotal, total }
    Responde: { id: string, redirect?: string }
    """
    try:
        data = request.data or {}
        payment = data.get("payment", {}) or {}
        metodo = str(payment.get("metodo", "")).lower()

        subtotal = Decimal(str(data.get("subtotal", 0) or 0))
        total = Decimal(str(data.get("total", 0) or 0))

        estado = "procesando" if metodo == "mercadopago" else "pendiente"

        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            subtotal=subtotal,
            total=total,
            estado=estado,
            items=data.get("items") or [],
            shipping=data.get("shipping") or {},
            shipping_quote=data.get("shippingQuote") or {},
            payment_info=payment,
        )

        redirect = None
        if metodo == "mercadopago":
            redirect = "https://www.mercadopago.com.ar/checkout"

        return Response({"id": order.id, "redirect": redirect}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({"detail": "Error al crear la orden"}, status=400)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_resumen(request):
    _require_admin(request.user)
    qs = Order.objects.all()
    totals = qs.aggregate(total=Sum("total"), subtotal=Sum("subtotal"))
    finalized = qs.filter(estado="entregado").count()

    total_orders = qs.count()
    total_revenue = totals.get("total") or 0

    response = {
        "totalOrders": total_orders,
        "totalRevenue": float(total_revenue),
        "avgTicket": float(total_revenue / total_orders) if total_orders else 0,
        "finalizedPct": (finalized / total_orders * 100) if total_orders else 0,
    }

    return Response(response)
