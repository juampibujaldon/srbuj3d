from django.urls import path, include 
from rest_framework import routers
from ventas import views


router = routers.DefaultRouter()
router.register(r'admin', views.AdminView, basename='Admin')
router.register(r'product', views.ProductView, basename='Product')
router.register(r'orders', views.OrderViewSet, basename='orders')
router.register(r'cart', views.CartView, basename='Cart')
router.register(r'payment', views.PaymentView, basename='Payment')
router.register(r'stlmodel', views.STLModelView, basename='STLModel')
router.register(r'sell', views.SellView, basename='Sell')

public_router = routers.DefaultRouter()
public_router.register(r'orders', views.OrderViewSet, basename='public-orders')

urlpatterns = [
    path('ventas/model', include(router.urls)),
    path('', include(public_router.urls)),
    path('health/', views.HealthCheckView.as_view(), name='health-check'),
    path('productos/', views.ProductListCreateView.as_view(), name='productos-list'),
    path('productos/<int:pk>/', views.ProductDetailView.as_view(), name='productos-detail'),
    # Endpoints específicos usados por el frontend
    path('files/uploads/', views.OrderFileUploadView.as_view(), name='orderfile-upload'),
    path('shipping/andreani/quote', views.AndreaniQuoteView.as_view(), name='andreani-quote'),
    path('features/', views.FeatureFlagListView.as_view(), name='feature-flags'),
    path('features/<str:key>/', views.FeatureFlagDetailView.as_view(), name='feature-flag-detail'),
    path('payments/confirm', views.PaymentConfirmView.as_view(), name='payment-confirm'),
    path('dashboard/resumen', views.dashboard_resumen, name='dashboard-resumen'),
    path('personalizador/cotizar-stl', views.STLQuoteView.as_view(), name='cotizar-stl'),
    path('stock', views.StockSnapshotView.as_view(), name='stock-snapshot'),
    path('stock/filaments', views.FilamentCollectionView.as_view(), name='stock-filaments'),
    path('stock/filaments/<str:identifier>', views.FilamentDetailView.as_view(), name='stock-filament-detail'),
    path('stock/filaments/<str:identifier>/adjust', views.FilamentAdjustView.as_view(), name='stock-filament-adjust'),
    path('stock/machines', views.MachineCollectionView.as_view(), name='stock-machines'),
    path('stock/machines/<str:identifier>', views.MachineDetailView.as_view(), name='stock-machine-detail'),
    path('stock/machines/<str:identifier>/maintenance', views.MachineMaintenanceView.as_view(), name='stock-machine-maintenance'),
    path('stock/machines/<str:identifier>/jobs/<int:job_id>/move', views.MachineJobMoveView.as_view(), name='stock-machine-job-move'),
    path('stock/machines/<str:identifier>/jobs/<int:job_id>/position', views.MachineJobPositionView.as_view(), name='stock-machine-job-position'),
    path('stock/reservations', views.ReservationView.as_view(), name='stock-reservation'),
    path('stock/reservations/<str:order_id>/consume', views.ReservationConsumeView.as_view(), name='stock-reservation-consume'),
    path('stock/reservations/<str:order_id>/release', views.ReservationReleaseView.as_view(), name='stock-reservation-release'),
    path('stock/atp/<str:sku>', views.AvailableToPromiseView.as_view(), name='stock-atp'),

]
