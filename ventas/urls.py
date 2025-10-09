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

]
