import logging
import os
import time
from datetime import datetime
from decimal import Decimal

import requests
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework import generics, mixins, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Admin, Cart, FeatureFlag, Order, OrderFile, Payment, Product, STLModel, Sell, User


logger = logging.getLogger(__name__)
from .serializer import (
    AdminSerializer,
    ProductSerializer,
    ProductPublicSerializer,
    OrderSerializer,
    OrderListSerializer,
    OrderFileSerializer,
    CartSerializer,
    PaymentSerializer,
    STLModelSerializer,
    SellSerializer,
    FeatureFlagSerializer,
)
from .throttles import FileUploadRateThrottle, ShippingQuoteAnonRateThrottle, ShippingQuoteRateThrottle

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


KNOWN_FEATURE_FLAGS = {"ENABLE_ANDREANI_QUOTE"}
FEATURE_DESCRIPTIONS = {
    "ENABLE_ANDREANI_QUOTE": "Habilita la integración con Andreani para cotizar envíos en tiempo real.",
}


def _flag_default(key: str) -> bool:
    env_value = os.getenv(key)
    if env_value is None:
        return False
    return str(env_value).strip().lower() in {"1", "true", "yes", "on"}


def is_feature_enabled(key: str) -> bool:
    if key not in KNOWN_FEATURE_FLAGS:
        return False
    try:
        flag = FeatureFlag.objects.get(key=key)
        return flag.enabled
    except FeatureFlag.DoesNotExist:
        return _flag_default(key)


def set_feature_flag(key: str, enabled: bool, user: User | None) -> FeatureFlag:
    if key not in KNOWN_FEATURE_FLAGS:
        raise ValueError(f"Feature flag desconocido: {key}")
    flag, _ = FeatureFlag.objects.get_or_create(
        key=key,
        defaults={
            "enabled": enabled,
            "updated_by": user,
            "description": FEATURE_DESCRIPTIONS.get(key, ""),
        },
    )
    if flag.enabled != enabled or flag.updated_by != user:
        flag.enabled = enabled
        if user:
            flag.updated_by = user
        update_fields = ["enabled", "updated_at"]
        if user:
            update_fields.append("updated_by")
        if not flag.description and FEATURE_DESCRIPTIONS.get(key):
            flag.description = FEATURE_DESCRIPTIONS[key]
            update_fields.append("description")
        flag.save(update_fields=update_fields)
    return flag


SAMPLE_PRODUCTS = [
    {
        "nombre": "Escultura David Neo",
        "autor": "SrBuj",
        "imagen_url": "/images/david.jpeg",
        "precio": Decimal("3500"),
        "descripcion": "Mini escultura del David con acabado neo; ideal para escritorio o estantería.",
        "mostrar_inicio": True,
    },
    {
        "nombre": "Mate Hogwarts",
        "autor": "SrBuj",
        "imagen_url": "/images/mate%20hogwarts.jpeg",
        "precio": Decimal("8900"),
        "descripcion": "Mate temático inspirado en Hogwarts. Perfecto para fans.",
        "mostrar_inicio": True,
    },
    {
        "nombre": "Mate Canon",
        "autor": "SrBuj",
        "imagen_url": "/images/mate%20canon.jpeg",
        "precio": Decimal("8700"),
        "descripcion": "Mate con estética fotográfica estilo Canon.",
        "mostrar_inicio": True,
    },
    {
        "nombre": "Joyero Ajedrez",
        "autor": "SrBuj",
        "imagen_url": "/images/joyero%20ajedrez.jpeg",
        "precio": Decimal("12500"),
        "descripcion": "Caja/joyero inspirado en el ajedrez con compartimentos internos.",
        "mostrar_inicio": True,
    },
    {
        "nombre": "Set Ajedrez Minimal",
        "autor": "SrBuj",
        "imagen_url": "/images/ser%20ajedrez.jpeg",
        "precio": Decimal("48000"),
        "descripcion": "Set de ajedrez impreso en 3D estilo minimal.",
        "mostrar_inicio": False,
    },
]


def _ensure_seed_data():
    if not Product.objects.exists():
        Product.objects.bulk_create(Product(**data) for data in SAMPLE_PRODUCTS)


_ANDREANI_TOKEN_CACHE = {"value": None, "expires": 0.0}

ALLOWED_UPLOAD_EXTENSIONS = {
    ".stl",
    ".step",
    ".obj",
    ".zip",
    ".rar",
    ".7z",
    ".png",
    ".jpg",
    ".jpeg",
    ".pdf",
}

MAX_UPLOAD_SIZE_BYTES = int(os.getenv("ORDER_FILE_MAX_MB", "30")) * 1024 * 1024


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


def _parse_date_param(raw_value: str | None, param: str, end_of_day: bool = False):
    if not raw_value:
        return None
    parsed = parse_datetime(raw_value)
    if parsed is None:
        date_value = parse_date(raw_value)
        if date_value is None:
            raise ValidationError({param: "Formato de fecha inválido. Usá ISO 8601 (YYYY-MM-DD)."})
        parsed = timezone.make_aware(
            datetime.combine(date_value, datetime.min.time()),
            timezone.get_current_timezone(),
        )
    elif timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
    if end_of_day:
        parsed = parsed.replace(hour=23, minute=59, second=59, microsecond=999999)
    return parsed


class OrdersPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50


class OrderViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated]
    pagination_class = OrdersPagination

    def get_queryset(self):
        qs = (
            Order.objects.select_related("user")
            .prefetch_related("items__product", "files")
            .order_by("-created_at")
        )
        user = self.request.user
        if not _is_admin(user):
            qs = qs.filter(user=user)

        status_param = self.request.query_params.get("status")
        if status_param:
            statuses = [
                status.strip()
                for status in status_param.split(",")
                if status.strip() in dict(Order.STATUS_CHOICES)
            ]
            if statuses:
                qs = qs.filter(status__in=statuses)

        date_from = _parse_date_param(self.request.query_params.get("from"), "from")
        if date_from:
            qs = qs.filter(created_at__gte=date_from)

        date_to = _parse_date_param(self.request.query_params.get("to"), "to", end_of_day=True)
        if date_to:
            qs = qs.filter(created_at__lte=date_to)

        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        if self.action in {"create", "update", "partial_update"}:
            return OrderSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        with transaction.atomic():
            order = serializer.save(user=self.request.user, status=Order.STATUS_DRAFT)
            order.refresh_amounts()
            logger.info(
                "order.created",
                extra={"order_id": order.id, "user_id": getattr(self.request.user, "id", None)},
            )

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        mutable_data = request.data.copy() if hasattr(request.data, "copy") else dict(request.data)
        status_value = mutable_data.pop("status", None)
        if status_value is not None:
            self._change_status(instance, status_value)
        serializer = self.get_serializer(instance, data=mutable_data, partial=True)
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data:
            self.perform_update(serializer)
        instance.refresh_from_db()
        output = self.get_serializer(instance)
        return Response(output.data)

    def perform_update(self, serializer):
        with transaction.atomic():
            order = serializer.save()
            order.refresh_amounts()
            logger.info(
                "order.updated",
                extra={"order_id": order.id, "user_id": getattr(self.request.user, "id", None)},
            )

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def submit(self, request, pk=None):
        order = self.get_object()
        if order.status != Order.STATUS_DRAFT:
            raise ValidationError({"status": "La orden ya fue enviada o procesada."})
        if not order.items.exists():
            raise ValidationError({"items": "Agregá al menos un producto antes de enviar la orden."})
        order.status = Order.STATUS_PENDING
        order.submitted_at = order.submitted_at or timezone.now()
        order.save(update_fields=["status", "submitted_at", "updated_at"])
        order.refresh_amounts()
        logger.info(
            "order.submitted",
            extra={"order_id": order.id, "user_id": getattr(request.user, "id", None)},
        )
        serializer = OrderSerializer(order, context=self.get_serializer_context())
        return Response(serializer.data)

    def _change_status(self, order: Order, new_status: str):
        normalized = str(new_status).lower()
        valid_statuses = {choice for choice, _ in Order.STATUS_CHOICES}
        if normalized not in valid_statuses:
            raise ValidationError({"status": "Estado inválido."})

        user = self.request.user
        is_admin = _is_admin(user)
        now = timezone.now()

        if not is_admin and normalized not in {Order.STATUS_CANCELLED, Order.STATUS_DRAFT}:
            raise PermissionDenied("No tenés permisos para actualizar el estado.")

        updates = ["status", "updated_at"]

        if normalized == Order.STATUS_DRAFT:
            if order.status != Order.STATUS_DRAFT:
                raise ValidationError({"status": "Solo un borrador puede volver a borrador."})
            order.status = Order.STATUS_DRAFT
        elif normalized == Order.STATUS_PENDING:
            if order.status not in {Order.STATUS_DRAFT, Order.STATUS_PENDING}:
                raise ValidationError({"status": "Solo un borrador puede pasar a pendiente."})
            order.status = Order.STATUS_PENDING
            if not order.submitted_at:
                order.submitted_at = now
                updates.append("submitted_at")
        elif normalized == Order.STATUS_PAID:
            if order.status not in {Order.STATUS_PENDING, Order.STATUS_PAID}:
                raise ValidationError({"status": "La orden necesita estar pendiente para marcarla como pagada."})
            order.status = Order.STATUS_PAID
            order.paid_at = now
            updates.append("paid_at")
        elif normalized == Order.STATUS_FULFILLED:
            if order.status not in {Order.STATUS_PAID, Order.STATUS_FULFILLED}:
                raise ValidationError({"status": "Marcá la orden como pagada antes de completarla."})
            order.status = Order.STATUS_FULFILLED
            order.fulfilled_at = now
            updates.append("fulfilled_at")
        elif normalized == Order.STATUS_CANCELLED:
            if order.status not in {Order.STATUS_DRAFT, Order.STATUS_PENDING, Order.STATUS_CANCELLED}:
                raise ValidationError({"status": "Solo borradores o pendientes pueden cancelarse."})
            order.status = Order.STATUS_CANCELLED
            order.cancelled_at = now
            updates.append("cancelled_at")

        order.save(update_fields=updates)
        logger.warning(
            "order.status_changed",
            extra={
                "order_id": order.id,
                "user_id": getattr(self.request.user, "id", None),
                "status": normalized,
            },
        )

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data.setdefault("meta", {})
        response.data["meta"]["feature_flags"] = {
            "ENABLE_ANDREANI_QUOTE": is_feature_enabled("ENABLE_ANDREANI_QUOTE")
        }
        return response


class OrderFileUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    throttle_classes = [FileUploadRateThrottle]

    def post(self, request):
        order_id = request.data.get("order")
        if not order_id:
            return Response({"detail": "Indicá el pedido a adjuntar."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            order = Order.objects.get(pk=order_id)
        except Order.DoesNotExist:
            return Response({"detail": "Pedido inexistente."}, status=status.HTTP_404_NOT_FOUND)

        if not _is_admin(request.user) and order.user != request.user:
            raise PermissionDenied("No podés adjuntar archivos a pedidos de otro usuario.")

        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response({"detail": "Adjuntá un archivo."}, status=status.HTTP_400_BAD_REQUEST)

        extension = os.path.splitext(uploaded_file.name)[1].lower()
        if extension not in ALLOWED_UPLOAD_EXTENSIONS:
            return Response(
                {
                    "detail": "Formato inválido. Permitidos: "
                    + ", ".join(sorted(ext.replace(".", "" ) for ext in ALLOWED_UPLOAD_EXTENSIONS)),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if uploaded_file.size > MAX_UPLOAD_SIZE_BYTES:
            max_mb = MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
            return Response(
                {"detail": f"El archivo supera el límite de {max_mb} MB."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        notes = request.data.get("notes", "")
        preview_url = request.data.get("preview_url", "")
        uploaded_ip = request.META.get("HTTP_X_FORWARDED_FOR") or request.META.get("REMOTE_ADDR")

        order_file = OrderFile.objects.create(
            order=order,
            file=uploaded_file,
            original_name=uploaded_file.name,
            uploaded_by=request.user if request.user.is_authenticated else None,
            notes=notes,
            preview_url=preview_url,
            uploaded_ip=(uploaded_ip or "")[:45],
        )

        logger.warning(
            "order.file_uploaded",
            extra={
                "order_id": order.id,
                "file_id": order_file.id,
                "user_id": getattr(request.user, "id", None),
                "size": uploaded_file.size,
                "ip": uploaded_ip,
            },
        )

        serializer = OrderFileSerializer(order_file, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


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


class PaymentConfirmView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payment_id = request.query_params.get("payment_id")
        if not payment_id:
            return Response({"detail": "Falta el parámetro payment_id."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payment = Payment.objects.select_related("order", "order__user").get(pk=payment_id)
        except Payment.DoesNotExist:
            return Response({"detail": "Pago inexistente."}, status=status.HTTP_404_NOT_FOUND)

        if not _is_admin(request.user) and payment.order.user != request.user:
            raise PermissionDenied("No podés consultar pagos de otro usuario.")

        is_paid = payment.estado == "aprobado"
        order = payment.order
        if is_paid and order.status not in {Order.STATUS_PAID, Order.STATUS_FULFILLED}:
            order.status = Order.STATUS_PAID
            if not order.paid_at:
                order.paid_at = timezone.now()
            order.save(update_fields=["status", "paid_at", "updated_at"])
            logger.info(
                "order.payment_confirmed",
                extra={"order_id": order.id, "payment_id": payment.id, "user_id": getattr(request.user, "id", None)},
            )

        return Response(
            {
                "payment_id": payment.id,
                "paid": is_paid,
                "status": payment.estado,
                "order_id": order.id,
                "order_status": order.status,
            }
        )


class FeatureFlagListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        data = {
            "flags": {
                key: {
                    "key": key,
                    "enabled": is_feature_enabled(key),
                    "description": FEATURE_DESCRIPTIONS.get(key, ""),
                }
                for key in KNOWN_FEATURE_FLAGS
            }
        }
        return Response(data)


class FeatureFlagDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, key):
        if key not in KNOWN_FEATURE_FLAGS:
            return Response({"detail": "Feature flag desconocido."}, status=status.HTTP_404_NOT_FOUND)
        flag = FeatureFlag.objects.filter(key=key).first()
        if flag:
            serializer = FeatureFlagSerializer(flag)
            data = serializer.data
        else:
            data = {
                "id": None,
                "key": key,
                "enabled": is_feature_enabled(key),
                "description": FEATURE_DESCRIPTIONS.get(key, ""),
                "updated_at": None,
            }
        return Response(data)

    def patch(self, request, key):
        _require_admin(request.user)
        if key not in KNOWN_FEATURE_FLAGS:
            return Response({"detail": "Feature flag desconocido."}, status=status.HTTP_404_NOT_FOUND)
        enabled_value = request.data.get("enabled")
        if enabled_value is None:
            raise ValidationError({"enabled": "Indicá si debe estar activo (true/false)."})
        if isinstance(enabled_value, str):
            enabled = enabled_value.strip().lower() in {"1", "true", "on", "si", "sí", "yes"}
        else:
            enabled = bool(enabled_value)

        flag = set_feature_flag(key, enabled, request.user)
        serializer = FeatureFlagSerializer(flag)
        return Response(serializer.data)


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

class AndreaniQuoteView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ShippingQuoteRateThrottle, ShippingQuoteAnonRateThrottle]

    def get(self, request):
        params = request.query_params
        postal_code = params.get("postal_code") or params.get("cpDestino")
        weight = params.get("weight") or params.get("pesoGr")
        if not postal_code or not weight:
            return Response(
                {"detail": "Indicá código postal y peso (en gramos)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            weight_gr = float(weight)
        except (TypeError, ValueError):
            return Response({"detail": "Peso inválido."}, status=status.HTTP_400_BAD_REQUEST)

        request_data = {
            "cpDestino": postal_code,
            "pesoGr": weight_gr,
            "provincia": params.get("provincia"),
            "localidad": params.get("localidad"),
            "altoCm": params.get("height") or params.get("altoCm"),
            "anchoCm": params.get("width") or params.get("anchoCm"),
            "largoCm": params.get("length") or params.get("largoCm"),
        }

        if not is_feature_enabled("ENABLE_ANDREANI_QUOTE"):
            return _fallback_andreani_quote(request_data, reason="Andreani deshabilitado", enabled=False)

        try:
            token = _obtener_token_andreani()
        except Exception as exc:  # noqa: BLE001
            logger.warning("andreani.token_error", exc_info=exc)
            return _fallback_andreani_quote(request_data, reason=str(exc))

        contrato = os.getenv("ANDREANI_CONTRATO")
        sucursal = os.getenv("ANDREANI_SUCURSAL")
        if not contrato:
            return Response({"detail": "Falta configurar ANDREANI_CONTRATO"}, status=status.HTTP_400_BAD_REQUEST)

        peso_kg = max(weight_gr / 1000.0, 0.1)
        payload = {
            "contrato": contrato,
            "origen": {
                "codigoPostal": os.getenv("ANDREANI_CP_ORIGEN", "1437"),
            },
            "destino": {
                "codigoPostal": postal_code,
                "localidad": params.get("localidad"),
                "provincia": params.get("provincia"),
            },
            "bultos": [
                {
                    "peso": {"valor": round(peso_kg, 3), "unidad": "kg"},
                    "volumen": {
                        "alto": float(request_data.get("altoCm") or 12),
                        "ancho": float(request_data.get("anchoCm") or 20),
                        "largo": float(request_data.get("largoCm") or 28),
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
        except requests.RequestException as exc:  # noqa: BLE001
            logger.warning("andreani.quote_error", exc_info=exc)
            return _fallback_andreani_quote(request_data, reason=f"Error Andreani: {exc}")

        info = resp.json() or {}
        tarifa = info.get("tarifa") or {}
        precio = tarifa.get("total") or tarifa.get("precioFinal")
        eta = info.get("plazoEntrega") or info.get("plazoEstimado")

        if precio is None:
            logger.warning("andreani.quote_unexpected", extra={"response": info})
            return _fallback_andreani_quote(request_data, reason="Andreani devolvió una respuesta inesperada", extra=info)

        return Response(
            {
                "precio": precio,
                "eta": eta or "",
                "enabled": True,
                "simulado": False,
            }
        )


def _fallback_andreani_quote(payload, reason="", extra=None, enabled=True):
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
        "enabled": enabled,
    }
    if reason:
        response["detalle"] = reason
    if extra:
        response["raw"] = extra
    return Response(response)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_resumen(request):
    _require_admin(request.user)
    qs = Order.objects.all()
    totals = qs.aggregate(total=Sum("total"), subtotal=Sum("subtotal"))
    finalized = qs.filter(status=Order.STATUS_FULFILLED).count()

    total_orders = qs.count()
    total_revenue = totals.get("total") or 0

    response = {
        "totalOrders": total_orders,
        "totalRevenue": float(total_revenue),
        "avgTicket": float(total_revenue / total_orders) if total_orders else 0,
        "finalizedPct": (finalized / total_orders * 100) if total_orders else 0,
    }

    return Response(response)
