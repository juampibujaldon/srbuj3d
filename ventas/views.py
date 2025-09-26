import os
import time
from decimal import Decimal

import requests
from django.db.models import Sum
from django.shortcuts import render
from rest_framework import viewsets, generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.views import APIView
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
        "mostrar_inicio": True,
    },
    {
        "nombre": "Mate Hogwarts",
        "autor": "SrBuj",
        "imagen_url": "/images/mate%20hogwarts.jpeg",
        "likes": 218,
        "downloads": 552,
        "precio": Decimal("8900"),
        "descripcion": "Mate temático inspirado en Hogwarts. Perfecto para fans.",
        "mostrar_inicio": True,
    },
    {
        "nombre": "Mate Canon",
        "autor": "SrBuj",
        "imagen_url": "/images/mate%20canon.jpeg",
        "likes": 175,
        "downloads": 410,
        "precio": Decimal("8700"),
        "descripcion": "Mate con estética fotográfica estilo Canon.",
        "mostrar_inicio": True,
    },
    {
        "nombre": "Joyero Ajedrez",
        "autor": "SrBuj",
        "imagen_url": "/images/joyero%20ajedrez.jpeg",
        "likes": 142,
        "downloads": 398,
        "precio": Decimal("12500"),
        "descripcion": "Caja/joyero inspirado en el ajedrez con compartimentos internos.",
        "mostrar_inicio": True,
    },
    {
        "nombre": "Set Ajedrez Minimal",
        "autor": "SrBuj",
        "imagen_url": "/images/ser%20ajedrez.jpeg",
        "likes": 289,
        "downloads": 720,
        "precio": Decimal("48000"),
        "descripcion": "Set de ajedrez impreso en 3D estilo minimal.",
        "mostrar_inicio": False,
    },
]


def _ensure_seed_data():
    if not Product.objects.exists():
        Product.objects.bulk_create(Product(**data) for data in SAMPLE_PRODUCTS)


_ANDREANI_TOKEN_CACHE = {"value": None, "expires": 0.0}


def _obtener_token_andreani():
    client_id = os.getenv("ANDREANI_CLIENT_ID")
    client_secret = os.getenv("ANDREANI_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise RuntimeError("Configurá ANDREANI_CLIENT_ID y ANDREANI_CLIENT_SECRET en el entorno")

    now = time.time()
    cached = _ANDREANI_TOKEN_CACHE
    if cached["value"] and cached["expires"] > now:
        return cached["value"]

    token_url = os.getenv("ANDREANI_TOKEN_URL", "https://apis.andreani.com/security/oauth/token")
    resp = requests.post(
        token_url,
        data={"grant_type": "client_credentials"},
        auth=(client_id, client_secret),
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    token = data.get("access_token")
    if not token:
        raise RuntimeError("Andreani no devolvió access_token")

    expires_in = int(data.get("expires_in", 900))
    cached["value"] = token
    cached["expires"] = now + max(expires_in - 30, 60)
    return token


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


class STLQuoteView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [AllowAny]

    MATERIAL_RATES = {
        "PLA": 0.25,
        "PETG": 0.3,
        "ABS": 0.35,
        "Resina": 0.45,
    }

    INFILL_MULTIPLIER = {
        "20": 1.0,
        "40": 1.15,
        "60": 1.3,
        "80": 1.5,
    }

    QUALITY_MULTIPLIER = {
        "draft": 0.9,
        "standard": 1.0,
        "fine": 1.25,
    }

    DEFAULT_DENSITY = {
        "PLA": 1.24,
        "PETG": 1.27,
        "ABS": 1.04,
        "Resina": 1.1,
    }

    def post(self, request):
        uploaded = request.FILES.get("stl") or request.FILES.get("file")
        if not uploaded:
            return Response({"error": "Debes adjuntar un archivo STL."}, status=status.HTTP_400_BAD_REQUEST)

        material = request.data.get("material", "PLA")
        infill = request.data.get("infill", "20")
        quality = request.data.get("quality", "standard")

        material_rate = self.MATERIAL_RATES.get(material, self.MATERIAL_RATES["PLA"])
        density = self.DEFAULT_DENSITY.get(material, 1.24)
        infill_factor = self.INFILL_MULTIPLIER.get(str(infill), 1.0)
        quality_factor = self.QUALITY_MULTIPLIER.get(quality, 1.0)

        import tempfile
        from stl import mesh

        try:
            with tempfile.NamedTemporaryFile(suffix=".stl") as tmp:
                for chunk in uploaded.chunks():
                    tmp.write(chunk)
                tmp.flush()
                model = mesh.Mesh.from_file(tmp.name)
                volume_mm3, _, _ = model.get_mass_properties()
        except Exception as exc:
            return Response(
                {"error": "No pudimos procesar el STL. Verificá el archivo.", "detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        volume_cm3 = max(volume_mm3 / 1000.0, 0)
        weight_g = volume_cm3 * density * infill_factor
        base_price = volume_cm3 * material_rate * infill_factor * quality_factor
        setup_cost = 3.5
        estimated_price = round(base_price + setup_cost, 2)
        print_speed_mm_s = 55 if quality != "fine" else 40
        estimated_time_hours = round((volume_mm3 / (print_speed_mm_s * 60 * 60)) * quality_factor * 1.5, 2)

        return Response(
            {
                "material": material,
                "infill": infill,
                "quality": quality,
                "volume_cm3": round(volume_cm3, 2),
                "weight_g": round(weight_g, 2),
                "estimated_time_hours": estimated_time_hours,
                "estimated_price": estimated_price,
                "file_size_mb": round(uploaded.size / (1024 * 1024), 3),
            }
        )

@api_view(["POST"])
@permission_classes([AllowAny])
def cotizar_andreani(request):
    data = request.data or {}

    try:
        token = _obtener_token_andreani()
    except Exception as exc:
        return _fallback_andreani_quote(data, reason=str(exc))

    contrato = os.getenv("ANDREANI_CONTRATO")
    sucursal = os.getenv("ANDREANI_SUCURSAL")
    if not contrato:
        return Response({"detail": "Falta configurar ANDREANI_CONTRATO"}, status=status.HTTP_400_BAD_REQUEST)

    peso_kg = max(float(data.get("pesoGr", 0) or 0) / 1000.0, 0.1)
    payload = {
        "contrato": contrato,
        "origen": {
            "codigoPostal": os.getenv("ANDREANI_CP_ORIGEN", "1437"),
        },
        "destino": {
            "codigoPostal": data.get("cpDestino"),
            "localidad": data.get("localidad"),
            "provincia": data.get("provincia"),
        },
        "bultos": [
            {
                "peso": {"valor": round(peso_kg, 3), "unidad": "kg"},
                "volumen": {
                    "alto": float(data.get("altoCm", 12) or 12),
                    "ancho": float(data.get("anchoCm", 20) or 20),
                    "largo": float(data.get("largoCm", 28) or 28),
                    "unidad": "cm",
                },
            }
        ],
    }

    if sucursal:
        payload["sucursalRetiro"] = sucursal

    cotizacion_url = os.getenv("ANDREANI_RATES_URL", "https://apis.andreani.com/v2/cotizaciones")

    try:
        resp = requests.post(
            cotizacion_url,
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        return _fallback_andreani_quote(data, reason=f"Error al consultar Andreani: {exc}")

    info = resp.json() or {}
    tarifa = info.get("tarifa") or {}
    precio = tarifa.get("total") or tarifa.get("precioFinal")
    eta = info.get("plazoEntrega") or info.get("plazoEstimado")

    if precio is None:
        return _fallback_andreani_quote(data, reason="Andreani devolvió una respuesta inesperada", extra=info)

    return Response({"precio": precio, "eta": eta or ""})


def _fallback_andreani_quote(payload, reason="", extra=None):
    try:
        peso_kg = max(float(payload.get("pesoGr", 0) or 0) / 1000.0, 0.1)
    except Exception:
        peso_kg = 0.1
    base = 2400
    variable = 850 * peso_kg
    precio = round(base + variable)
    response = {
        "precio": precio,
        "eta": "3-5 días hábiles",
        "simulado": True,
    }
    if reason:
        response["detalle"] = reason
    if extra:
        response["raw"] = extra
    return Response(response)


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
