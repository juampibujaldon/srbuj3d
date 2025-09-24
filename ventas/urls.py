from django.urls import path, include 
from rest_framework import routers
from ventas import views


router = routers.DefaultRouter()
router.register(r'admin', views.AdminView, basename='Admin')
router.register(r'product', views.ProductView, basename='Product')
router.register(r'order', views.OrderView, basename='Order')
router.register(r'cart', views.CartView, basename='Cart')
router.register(r'payment', views.PaymentView, basename='Payment')
router.register(r'stlmodel', views.STLModelView, basename='STLModel')
router.register(r'sell', views.SellView, basename='Sell')

urlpatterns = [
    path('ventas/model', include(router.urls)),
    path('productos/', views.ProductListCreateView.as_view(), name='productos-list'),
    path('productos/<int:pk>/', views.ProductDetailView.as_view(), name='productos-detail'),
    # Endpoints específicos usados por el frontend
    path('andreani/cotizar', views.cotizar_andreani, name='andreani-cotizar'),
    path('ordenes', views.crear_orden, name='crear-orden'),
    path('ordenes/admin', views.OrderListView.as_view(), name='ordenes-admin'),
    path('ordenes/<int:pk>/estado', views.OrderStatusUpdateView.as_view(), name='ordenes-estado'),
    path('dashboard/resumen', views.dashboard_resumen, name='dashboard-resumen'),

]
